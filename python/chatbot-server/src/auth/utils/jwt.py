"""JWT creation and verification for auth and refresh tokens."""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt

from src.settings import settings
from src.utils.logging import get_logger

_logger = get_logger(__name__)

TOKEN_KIND_AUTH = "auth"
TOKEN_KIND_REFRESH = "refresh"

ENTITY_TYPE_USER = "user"
ENTITY_TYPE_SERVICE_ACCOUNT = "service_account"


@dataclass(frozen=True)
class TokenPayload:
    """Decoded token payload with entity type and id."""

    entity_type: str
    entity_id: str


def create_auth_token(
    entity_id: str,
    *,
    entity_type: str = ENTITY_TYPE_USER,
) -> str:
    """Create a short-lived auth JWT (default 15 min)."""
    return _create_token(
        entity_type, entity_id, TOKEN_KIND_AUTH, settings.JWT_AUTH_TTL_SECONDS
    )


def create_refresh_token(
    entity_id: str,
    *,
    entity_type: str = ENTITY_TYPE_USER,
) -> str:
    """Create a long-lived refresh JWT (default 24 h)."""
    return _create_token(
        entity_type, entity_id, TOKEN_KIND_REFRESH, settings.JWT_REFRESH_TTL_SECONDS
    )


def _create_token(
    entity_type: str, entity_id: str, token_kind: str, ttl_seconds: int
) -> str:
    secret = settings.JWT_SECRET_KEY
    if secret is None:
        raise ValueError("JWT_SECRET_KEY is not set")
    now = int(time.time())
    payload = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "type": token_kind,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(
        payload,
        secret.get_secret_value(),
        algorithm="HS256",
    )


def verify_refresh_token(token: str) -> TokenPayload | None:
    """Verify a refresh token and return TokenPayload, or None if invalid."""
    return _verify_token(token, TOKEN_KIND_REFRESH)


def verify_auth_token(token: str) -> TokenPayload | None:
    """Verify an auth token and return TokenPayload, or None if invalid."""
    return _verify_token(token, TOKEN_KIND_AUTH)


def _verify_token(token: str, expected_kind: str) -> TokenPayload | None:
    secret = settings.JWT_SECRET_KEY
    if secret is None:
        return None
    try:
        payload = jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=["HS256"],
        )
        if payload.get("type") != expected_kind:
            return None
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")
        if not entity_type or not entity_id:
            return None
        return TokenPayload(entity_type=str(entity_type), entity_id=str(entity_id))
    except jwt.PyJWTError:
        return None
    except Exception as e:
        _logger.warning("JWT verification failed: %s", e, exc_info=True)
        return None
