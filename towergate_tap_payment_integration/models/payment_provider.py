# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools.urls import urljoin

from odoo.addons.towergate_tap_payment_integration import const


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(selection_add=[("tap", "Tap")], ondelete={"tap": "set default"})
    tap_secret_key = fields.Char(
        string="Tap Secret Key",
        help="The secret API key of the Tap account (sk_test_... or sk_live_...).",
        required_if_provider="tap",
        copy=False,
        groups="base.group_system",
    )
    tap_merchant_id = fields.Char(
        string="Tap Merchant ID",
        help="Optional. The merchant id to send with each charge, if the account requires it.",
        copy=False,
    )

    # === COMPUTE METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to restrict Tap to the currencies it accepts."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "tap":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        self.ensure_one()
        if self.code != "tap":
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the Tap API URL."""
        if self.code != "tap":
            return super()._build_request_url(endpoint, **kwargs)
        return urljoin(const.API_URL, endpoint)

    def _build_request_headers(self, *args, **kwargs):
        """Override of `payment` to authenticate with the secret key."""
        if self.code != "tap":
            return super()._build_request_headers(*args, **kwargs)
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.tap_secret_key}",
        }

    def _parse_response_error(self, response):
        """Override of `payment` to extract Tap's error message."""
        if self.code != "tap":
            return super()._parse_response_error(response)
        errors = response.json().get("errors") or []
        return "\n".join(e.get("description", "") for e in errors) or response.text
