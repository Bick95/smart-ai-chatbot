"""Password hashing utilities using bcrypt (0-trust: never store plain passwords)."""

from __future__ import annotations

from passlib.hash import bcrypt

# Use bcrypt_sha256 for passwords > 72 bytes; bcrypt truncates by default
# bcrypt is sufficient for typical passwords
_hasher = bcrypt.using(rounds=12)


def hash_password(password: str) -> str:
    """Hash a plain password for secure storage."""
    return _hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a stored hash."""
    return _hasher.verify(plain, hashed)
