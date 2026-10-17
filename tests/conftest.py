"""Shared pytest bootstrap for GrantThrive backend tests.

These values are deterministic, non-production test keys. They are set before
application modules import the field-encryption service so CI exercises the
same encrypted-column path as production without depending on deployment
secrets.
"""

import os


os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY",
    "Z3JhbnR0aHJpdmUtdGVzdC1lbmNyeXB0aW9uLWtleSE=",
)
os.environ.setdefault(
    "FIELD_HMAC_KEY",
    "Z3JhbnR0aHJpdmUtdGVzdC1obWFjLWtleS0wMDAwMDA=",
)
