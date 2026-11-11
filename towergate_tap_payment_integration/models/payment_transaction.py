# -*- coding: utf-8 -*-
import re
from urllib.parse import urlparse

from odoo import api, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain
from odoo.tools.urls import urljoin

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.towergate_tap_payment_integration import const
from odoo.addons.towergate_tap_payment_integration.controllers.main import TapController

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # === LIFECYCLE METHODS - PAYMENT FORM === #

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to create the Tap charge and return the redirect form values.

        Note: `self.ensure_one()` from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values.
        :return: The values used to render `payment.generic_redirect_form`.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "tap":
            return res

        base_url = self.provider_id.get_base_url()
        first_name, last_name = payment_utils.split_partner_name(self.partner_name or "")
        payload = {
            "amount": self.amount,
            "currency": self.currency_id.name,
            "threeDSecure": True,
            "save_card": False,
            "customer_initiated": True,
            "description": self.reference,
            "statement_descriptor": (self.company_id.name or "")[:22],
            "reference": {"transaction": self.reference, "order": self.reference},
            "receipt": {"email": True, "sms": True},
            "customer": {
                "first_name": first_name,
                "last_name": last_name,
                "email": self.partner_email,
                "phone": {
                    "country_code": str(self.partner_country_id.phone_code or ""),
                    "number": re.sub(r"\D", "", self.partner_phone or ""),
                },
            },
            "source": {"id": "src_all"},
            "post": {"url": urljoin(base_url, TapController._webhook_url)},
            "redirect": {"url": urljoin(base_url, TapController._return_url)},
        }
        if self.provider_id.tap_merchant_id:
            payload["merchant"] = {"id": self.provider_id.tap_merchant_id}

        try:
            charge_data = self._send_api_request("POST", "charges", json=payload)
        except ValidationError as error:
            self._set_error(str(error))
            return {}

        payment_url = charge_data.get("transaction", {}).get("url")
        if not payment_url:
            self._set_error(self.env._("Tap did not return a payment URL."))
            return {}

        # Remember the charge id to find the transaction back when the customer returns.
        self.provider_reference = charge_data.get("id")

        # Query-string params are stripped by browsers on GET form submission, so they are passed
        # as hidden inputs of the generic redirect form instead.
        parsed_url = urlparse(payment_url)
        return {
            "api_url": parsed_url._replace(query="").geturl(),
            "http_method": "get",
            "url_params": payment_utils.extract_url_params(payment_url),
        }

    # === LIFECYCLE METHODS - PAYLOAD RECEPTION === #

    @api.model
    def _tap_get_tx_from_charge_id(self, charge_id):
        """Return the Tap transaction whose provider reference is the given charge id.

        :param str charge_id: The Tap charge id (`chg_...`).
        :return: The transaction, if found.
        :rtype: payment.transaction
        """
        tx = self.search(
            Domain("provider_reference", "=", charge_id) & Domain("provider_code", "=", "tap"),
            limit=1,
        )
        if not tx:
            _logger.warning("No Tap transaction found matching charge id %s.", charge_id)
        return tx

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to read the reference Odoo sent in the charge."""
        if provider_code != "tap":
            return super()._extract_reference(provider_code, payment_data)
        return (payment_data.get("reference") or {}).get("transaction")

    # === LIFECYCLE METHODS - PROCESSING === #

    def _extract_amount_data(self, payment_data):
        """Override of `payment` to let the framework check the paid amount and currency."""
        if self.provider_code != "tap":
            return super()._extract_amount_data(payment_data)
        return {
            "amount": float(payment_data.get("amount") or 0),
            "currency_code": payment_data.get("currency"),
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction state from the Tap charge status."""
        if self.provider_code != "tap":
            return super()._apply_updates(payment_data)

        if payment_data.get("id"):
            self.provider_reference = payment_data["id"]

        status = (payment_data.get("status") or "").upper()
        if status in const.PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING["done"]:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING["cancel"]:
            self._set_canceled()
        elif status in const.PAYMENT_STATUS_MAPPING["error"]:
            message = (payment_data.get("response") or {}).get("message", "")
            self._set_error(self.env._("The payment was refused by Tap (%s). %s", status, message))
        else:
            _logger.warning(
                "Received data with invalid payment status (%s) for transaction %s.",
                status,
                self.reference,
            )
            self._set_error(self.env._("Unknown payment status: %s", status))
