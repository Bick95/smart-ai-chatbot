"""Shared validation utilities."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from pydantic import BeforeValidator, ValidationInfo

from src.utils.logging import get_logger

_logger = get_logger(__name__)


def _uuid4_validator(v: Any, info: ValidationInfo) -> str:
    """Validator for Uuid4Str: coerces to str and validates UUID-v4."""
    s = str(v) if not isinstance(v, str) else v
    field_name = getattr(info, "field_name", None) or "value"
    return validate_uuid4(s, field_name=field_name)


# Type alias for UUID-v4 validated string fields. Use instead of str for IDs.
Uuid4Str = Annotated[str, BeforeValidator(_uuid4_validator)]


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


def validate_uuid4(value: str, *, field_name: str = "value") -> str:
    """Validate and return value as UUID-v4 string. Raises ValueError if invalid."""
    if not is_valid_uuid4(value):
        raise ValueError(f"{field_name} must be UUID-v4, got {value!r}")
    return value
