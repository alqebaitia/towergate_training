# Towergate Tap Payment Integration (Odoo 20)

Ported from `bi_tap_payment_acquire` (Odoo 18).

## Setup
1. Install the module (Apps → Towergate Tap Payment Integration).
2. Invoicing/Website → Configuration → Payment Providers → **Tap**.
3. Enter the **Secret Key** (`sk_test_...` for test mode, `sk_live_...` once *Enabled/Live*).
4. Optional: enter the **Merchant ID** if your Tap account requires it.
5. Publish the provider and set the payment journal.

## Flow
Checkout → `charges` API (POST) → redirect to Tap hosted page → customer returns on
`/payment/tap/return?tap_id=chg_...` (and Tap posts to `/payment/tap/webhook`) →
charge re-fetched from the API → `_record()` → `_apply_updates()` sets the state.
