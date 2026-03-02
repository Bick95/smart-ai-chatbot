"""Auth domain types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.utils.logging import get_logger

_logger = get_logger(__name__)


@dataclass(frozen=True)
class AuthUser:
    """Represents an authenticated user."""

    id: str
    email: str
    username: str
    created_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthUser:
        """Build AuthUser from a dictionary (e.g. DB row or API response)."""
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        elif created is not None and not isinstance(created, datetime):
            _logger.warning(
                "AuthUser.from_dict: created_at has unexpected type %s; setting to None",
                type(created).__name__,
            )
            created = None
        return cls(
            id=str(data["id"]),
            email=str(data["email"]),
            username=str(data.get("username", data.get("user_metadata", {}).get("username", ""))),
            created_at=created,
        )
