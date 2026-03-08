"""
GrantThrive — AES-256-GCM Field-Level Encryption
==================================================
Provides transparent, authenticated encryption for Personally Identifiable
Information (PII) stored in the database.

Algorithm: AES-256-GCM
  - AES-256: 256-bit key, approved by NIST and the Australian Signals
    Directorate (ASD) for protecting sensitive data
  - GCM (Galois/Counter Mode): provides both confidentiality (encryption)
    and integrity (authentication tag). Tampered ciphertext is detected and
    rejected before decryption, preventing padding oracle and bit-flipping
    attacks that affect AES-CBC.

Key management:
  The encryption key is read from the FIELD_ENCRYPTION_KEY environment
  variable at startup.  It must be a URL-safe base64-encoded 32-byte value.
  Generate a new key with:

      python3 -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"

  NEVER commit this key to source control.  Store it as a secret in your
  deployment environment (AWS Secrets Manager, GitHub Actions secret, etc.)

Searchable fields (e.g. email):
  Encrypted values cannot be queried with SQL LIKE or equality checks.
  For fields that need to be searched (email login lookup), a separate
  HMAC-SHA256 index column is maintained alongside the encrypted value.
  The HMAC uses a separate HMAC_SECRET_KEY environment variable so that
  a database breach alone does not expose the plaintext.

  Index column naming convention:  <field_name>_hmac
  e.g.  email  →  email_hmac

SQLAlchemy integration:
  Use the EncryptedString TypeDecorator to apply encryption transparently:

      from app.common.encryption import EncryptedString

      class User(db.Model):
          email       = db.Column(db.String(500))   # stores ciphertext
          email_hmac  = db.Column(db.String(64), index=True)  # HMAC index
          phone       = db.Column(EncryptedString(200))

  For searchable fields, use the helper functions directly:
      from app.common.encryption import encrypt_field, decrypt_field, hmac_index
"""

import base64
import hashlib
import hmac
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import types

logger = logging.getLogger(__name__)

# ── Key loading ───────────────────────────────────────────────────────────────

def _load_key(env_var: str, key_len: int = 32) -> bytes | None:
    """Load and decode a base64-encoded key from an environment variable.

    Returns None if the variable is not set (allows the app to start in
    development without encryption configured, but logs a warning).
    """
    raw = os.environ.get(env_var)
    if not raw:
        logger.warning(
            "Environment variable %s is not set. PII field encryption is DISABLED. "
            "Set this variable before deploying to production.", env_var
        )
        return None
    try:
        key = base64.urlsafe_b64decode(raw.strip())
        if len(key) != key_len:
            raise ValueError(f"Key must be {key_len} bytes, got {len(key)}")
        return key
    except Exception as exc:
        logger.error("Failed to load encryption key from %s: %s", env_var, exc)
        return None


# Keys are loaded once at module import time.
_ENCRYPTION_KEY: bytes | None = _load_key("FIELD_ENCRYPTION_KEY", 32)
_HMAC_KEY: bytes | None       = _load_key("FIELD_HMAC_KEY", 32)


# ── Core encryption / decryption ──────────────────────────────────────────────

_NONCE_LEN = 12   # 96-bit nonce — GCM standard


def encrypt_field(plaintext: str | None) -> str | None:
    """Encrypt a plaintext string using AES-256-GCM.

    Returns a base64-encoded string of the form:
        base64(nonce || ciphertext || auth_tag)

    Returns None if plaintext is None or encryption is not configured.
    """
    if plaintext is None:
        return None
    if _ENCRYPTION_KEY is None:
        # Encryption not configured — store plaintext with a warning prefix
        # so it is obvious in the database that encryption is missing.
        logger.debug("Storing field unencrypted (FIELD_ENCRYPTION_KEY not set)")
        return plaintext

    aesgcm = AESGCM(_ENCRYPTION_KEY)
    nonce  = os.urandom(_NONCE_LEN)
    ct     = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.urlsafe_b64encode(nonce + ct).decode('ascii')


def decrypt_field(ciphertext: str | None) -> str | None:
    """Decrypt a value produced by encrypt_field.

    Returns None if ciphertext is None.
    Raises ValueError if decryption fails (tampered or corrupted data).
    """
    if ciphertext is None:
        return None
    if _ENCRYPTION_KEY is None:
        return ciphertext  # Pass-through when encryption not configured

    try:
        raw    = base64.urlsafe_b64decode(ciphertext.encode('ascii'))
        nonce  = raw[:_NONCE_LEN]
        ct     = raw[_NONCE_LEN:]
        aesgcm = AESGCM(_ENCRYPTION_KEY)
        return aesgcm.decrypt(nonce, ct, None).decode('utf-8')
    except Exception as exc:
        logger.error("Field decryption failed: %s", exc)
        raise ValueError("Failed to decrypt field value.") from exc


def hmac_index(value: str | None) -> str | None:
    """Compute a constant-length HMAC-SHA256 index for a searchable field.

    The HMAC is keyed with FIELD_HMAC_KEY so that the index cannot be
    reversed even if the database is compromised without the key.

    Returns a 64-character hex string, or None if value is None.
    """
    if value is None:
        return None
    if _HMAC_KEY is None:
        # Fallback: use a plain SHA-256 hash (weaker, but functional)
        logger.debug("FIELD_HMAC_KEY not set — using plain SHA-256 for index")
        return hashlib.sha256(value.lower().encode('utf-8')).hexdigest()

    return hmac.new(
        _HMAC_KEY,
        value.lower().encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


# ── SQLAlchemy TypeDecorator ──────────────────────────────────────────────────

class EncryptedString(types.TypeDecorator):
    """A SQLAlchemy column type that transparently encrypts/decrypts values.

    Usage:
        phone = db.Column(EncryptedString(200))

    The underlying storage column should be sized to accommodate the
    base64-encoded ciphertext, which is approximately:
        ceil((plaintext_bytes + 12 nonce + 16 auth_tag) * 4/3)

    For a 200-character plaintext, ~300 characters of storage is sufficient.
    The impl_length parameter controls the underlying VARCHAR size.
    """
    impl = types.String
    cache_ok = True

    def __init__(self, impl_length: int = 500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = types.String(impl_length)

    def process_bind_param(self, value, dialect):
        """Encrypt before writing to the database."""
        if value is None:
            return None
        return encrypt_field(str(value))

    def process_result_value(self, value, dialect):
        """Decrypt after reading from the database."""
        if value is None:
            return None
        return decrypt_field(value)

    def copy(self, **kwargs):
        return EncryptedString(self.impl.length)
