# -*- coding: utf-8 -*-
from . import controllers, models

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    """Activate the default payment methods, duplicate the provider in every company and
    create the matching `account.payment.method` (done by `account_payment`)."""
    setup_provider(env, "tap")


def uninstall_hook(env):
    """Reset the provider to `none` and remove its accounting payment method."""
    reset_payment_provider(env, "tap")
