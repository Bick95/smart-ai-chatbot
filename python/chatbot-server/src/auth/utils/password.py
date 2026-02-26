"""Password hashing utilities using Argon2id (0-trust: never store plain passwords)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from src.utils.logging import get_logger

_logger = get_logger(__name__)
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plain password for secure storage."""
    return _hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a stored hash.

    Returns False on wrong password, invalid hash, or any unexpected error.
    """
    try:
        _hasher.verify(hashed, plain)
        return True
    except (InvalidHashError, VerificationError):
        return False
    except Exception as e:
        _logger.exception("Unexpected error in verify_password: %s", e)
        return False
