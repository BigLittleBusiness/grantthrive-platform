"""
GrantThrive — Argon2id Password Hashing
=========================================
Replaces Werkzeug's PBKDF2-HMAC-SHA256 with Argon2id, the winner of the
Password Hashing Competition (2015) and the current recommendation from
OWASP, NIST, and the Australian Signals Directorate.

Why Argon2id over PBKDF2:
  - Memory-hard: requires significant RAM per attempt, making GPU-based
    brute-force attacks orders of magnitude more expensive
  - Side-channel resistant: the 'id' variant combines Argon2i (side-channel
    resistance) and Argon2d (GPU resistance)
  - Tunable: parameters can be increased as hardware improves without
    invalidating existing hashes (rehash-on-login pattern)

Parameters (OWASP recommended minimums as of 2024):
  - time_cost:    3 iterations
  - memory_cost:  65536 KiB (64 MB)
  - parallelism:  4 threads
  - hash_len:     32 bytes
  - salt_len:     16 bytes

Backward compatibility:
  Existing PBKDF2 hashes (Werkzeug format: "pbkdf2:sha256:...") are
  detected and verified using Werkzeug, then transparently rehashed to
  Argon2id on the next successful login.
"""

import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

logger = logging.getLogger(__name__)

# ── Argon2id hasher — OWASP 2024 recommended parameters ──────────────────────
_hasher = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # 64 MB in KiB
    parallelism=4,      # Parallel threads
    hash_len=32,        # Output hash length in bytes
    salt_len=16,        # Random salt length in bytes
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id.

    Returns a self-contained encoded string that includes the algorithm,
    parameters, salt, and hash — safe to store directly in the database.

    Args:
        password: The plaintext password string.

    Returns:
        An Argon2id encoded hash string.
    """
    return _hasher.hash(password)


def verify_password(stored_hash: str, password: str) -> tuple[bool, bool]:
    """Verify a password against a stored hash.

    Handles both Argon2id hashes and legacy Werkzeug PBKDF2 hashes
    transparently, enabling a zero-downtime migration.

    Args:
        stored_hash: The hash string from the database.
        password:    The plaintext password to verify.

    Returns:
        A tuple (is_valid, needs_rehash) where:
          - is_valid:    True if the password matches the hash
          - needs_rehash: True if the hash should be upgraded to Argon2id
                          (i.e. it was a legacy PBKDF2 hash, or Argon2id
                          parameters have been updated since the hash was
                          created)
    """
    # ── Detect legacy Werkzeug PBKDF2 hashes ─────────────────────────────────
    if stored_hash.startswith('pbkdf2:') or stored_hash.startswith('scrypt:'):
        from werkzeug.security import check_password_hash as _werkzeug_check
        try:
            is_valid = _werkzeug_check(stored_hash, password)
            return is_valid, is_valid  # needs_rehash=True if password was correct
        except Exception as exc:
            logger.warning("Legacy hash verification error: %s", exc)
            return False, False

    # ── Argon2id verification ─────────────────────────────────────────────────
    try:
        _hasher.verify(stored_hash, password)
        # Check if parameters have changed since this hash was created
        needs_rehash = _hasher.check_needs_rehash(stored_hash)
        return True, needs_rehash
    except VerifyMismatchError:
        return False, False
    except (VerificationError, InvalidHashError) as exc:
        logger.warning("Argon2 verification error: %s", exc)
        return False, False


def needs_rehash(stored_hash: str) -> bool:
    """Return True if the hash should be upgraded.

    Covers both legacy PBKDF2 hashes and Argon2id hashes with outdated
    parameters.
    """
    if stored_hash.startswith('pbkdf2:') or stored_hash.startswith('scrypt:'):
        return True
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except Exception:
        return True
