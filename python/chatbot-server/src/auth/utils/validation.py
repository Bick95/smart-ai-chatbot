"""Auth validation helpers."""

from __future__ import annotations

import uuid

from src.utils.logging import get_logger

_logger = get_logger(__name__)


def is_valid_uuid4(value: str) -> bool:
    """Return True if value is a valid UUID-v4 string."""
    try:
        u = uuid.UUID(value)
        return u.version == 4
    except (ValueError, TypeError, AttributeError):
        return False
    except Exception as e:
        _logger.warning(
            "is_valid_uuid4: unexpected %s",
            type(e).__name__,
            exc_info=True,
        )
        raise


def validate_uuid4(value: str) -> str:
    """Validate and return value as UUID-v4 string. Raises ValueError if invalid."""
    if not is_valid_uuid4(value):
        raise ValueError(f"Invalid UUID-v4: {value!r}")
    return value
