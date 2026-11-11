-- disable Tap payment provider credentials on neutralized (test/staging) databases
UPDATE payment_provider
   SET tap_secret_key = NULL;
