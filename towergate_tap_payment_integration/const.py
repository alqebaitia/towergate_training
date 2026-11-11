# -*- coding: utf-8 -*-

# Base URL of the Tap REST API.
API_URL = "https://api.tap.company/v2/"

# The currencies supported by Tap, in ISO 4217 format.
SUPPORTED_CURRENCIES = ["KWD", "USD", "SAR", "AED", "QAR", "BHD", "OMR", "EGP", "EUR", "GBP"]

# The codes of the default payment methods to activate when the module is installed.
DEFAULT_PAYMENT_METHOD_CODES = {"tap"}

# Mapping of Odoo transaction states to Tap charge statuses.
PAYMENT_STATUS_MAPPING = {
    "pending": ("INITIATED", "IN_PROGRESS"),
    "done": ("AUTHORIZED", "CAPTURED"),
    "cancel": ("ABANDONED", "VOID", "CANCELLED", "TIMEDOUT"),
    "error": ("FAILED", "DECLINED", "RESTRICTED", "UNKNOWN"),
}

# Keys that must never appear in clear text in the logs.
SENSITIVE_KEYS = {"Authorization"}
