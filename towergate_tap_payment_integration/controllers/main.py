# -*- coding: utf-8 -*-
import pprint

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger

_logger = get_payment_logger(__name__)


class TapController(http.Controller):
    _return_url = "/payment/tap/return"
    _webhook_url = "/payment/tap/webhook"

    @http.route(
        _return_url,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def tap_return_from_checkout(self, **data):
        """Process the redirection from the Tap hosted checkout.

        Tap appends `?tap_id=chg_xxx` to the redirect URL. The charge is never trusted as sent by
        the browser: it is fetched again from the Tap API before being recorded.

        The route is flagged with `save_session=False` so that Odoo does not assign a new session
        to the customer if the browser drops the session cookie on the cross-site redirection.

        :param dict data: The query-string parameters sent by Tap.
        :return: The redirection to the payment status page.
        """
        _logger.info("Handling redirection from Tap with data:\n%s", pprint.pformat(data))
        charge_id = data.get("tap_id")
        if charge_id:
            tx_sudo = request.env["payment.transaction"].sudo()._tap_get_tx_from_charge_id(
                charge_id
            )
            self._verify_and_record(tx_sudo, charge_id)
        return request.redirect("/payment/status")

    @http.route(_webhook_url, type="http", auth="public", methods=["POST"], csrf=False)
    def tap_webhook(self):
        """Process the charge notification that Tap posts to the webhook (`post.url`).

        :return: An empty JSON response to acknowledge the notification.
        """
        try:
            data = request.get_json_data()
        except ValueError:
            data = dict(request.get_http_params())
        _logger.info("Notification received from Tap with data:\n%s", pprint.pformat(data))

        tx_sudo = request.env["payment.transaction"].sudo()._search_by_reference("tap", data)
        if not tx_sudo and data.get("id"):
            tx_sudo = request.env["payment.transaction"].sudo()._tap_get_tx_from_charge_id(
                data["id"]
            )
        self._verify_and_record(tx_sudo, data.get("id"))
        # Always acknowledge the notification so that Tap doesn't keep retrying it.
        return request.make_json_response("")

    @staticmethod
    def _verify_and_record(tx_sudo, charge_id):
        """Fetch the charge from the Tap API and record it on the transaction.

        :param payment.transaction tx_sudo: The transaction, in sudo mode (may be empty).
        :param str charge_id: The Tap charge id (`chg_...`).
        :rtype: None
        """
        if not tx_sudo or not charge_id:
            return
        try:
            charge_data = tx_sudo._send_api_request("GET", f"charges/{charge_id}")
        except ValidationError:
            _logger.exception("Unable to verify the Tap charge %s.", charge_id)
        else:
            tx_sudo._record(charge_data)
