"""Auth domain types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthUser:
    """Represents an authenticated user."""

    id: str
    email: str
    username: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthUser:
        """Build AuthUser from a dictionary (e.g. DB row or API response)."""
        return cls(
            id=str(data["id"]),
            email=str(data["email"]),
            username=str(data.get("username", data.get("user_metadata", {}).get("username", ""))),
        )
