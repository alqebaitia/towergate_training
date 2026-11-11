# -*- coding: utf-8 -*-
{
    "name": "Towergate Tap Payment Integration",
    "version": "20.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "sequence": 350,
    "summary": "Accept online payments through the Tap Payments hosted checkout "
               "(Kuwait, Saudi Arabia, UAE, Bahrain, Qatar, Oman, Egypt).",
    "description": """
Tap Payment Gateway integration for Odoo 20.

Customers are redirected to the Tap hosted checkout page, and the payment
result is fetched back from the Tap Charges API on return and on webhook
notification, then processed by Odoo's standard payment pipeline.
""",
    "depends": ["payment", "account_payment", "website_sale", "sale_management", "auth_signup"],
    "data": [
        "views/payment_provider_views.xml",
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "auto_install": False,
    "license": "OPL-1",
}
