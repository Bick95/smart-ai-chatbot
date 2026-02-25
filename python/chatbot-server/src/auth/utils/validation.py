"""Auth validation helpers."""

from __future__ import annotations

import uuid


def is_valid_uuid4(value: str) -> bool:
    """Return True if value is a valid UUID-v4 string."""
    try:
        u = uuid.UUID(value)
        return u.version == 4
    except (ValueError, TypeError, AttributeError):
        return False


def validate_uuid4(value: str) -> str:
    """Validate and return value as UUID-v4 string. Raises ValueError if invalid."""
    if not is_valid_uuid4(value):
        raise ValueError(f"Invalid UUID-v4: {value!r}")
    return value
