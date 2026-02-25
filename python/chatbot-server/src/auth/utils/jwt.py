"""JWT creation and verification for auth and refresh tokens."""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt

from src.settings import settings
from src.utils.logging import get_logger

_logger = get_logger(__name__)

TOKEN_TYPE_AUTH = "auth"
TOKEN_TYPE_REFRESH = "refresh"

SUBJECT_TYPE_USER = "user"
SUBJECT_TYPE_SERVICE_ACCOUNT = "service_account"


@dataclass(frozen=True)
class SubjectPayload:
    """Subject claim extracted from a decoded token (who can act on the system)."""

    subject_type: str
    subject_id: str


def create_auth_token(
    subject_id: str,
    *,
    subject_type: str = SUBJECT_TYPE_USER,
) -> str:
    """Create a short-lived auth JWT (default 15 min)."""
    return _create_token(
        subject_type, subject_id, TOKEN_TYPE_AUTH, settings.JWT_AUTH_TTL_SECONDS
    )


def create_refresh_token(
    subject_id: str,
    *,
    subject_type: str = SUBJECT_TYPE_USER,
) -> str:
    """Create a long-lived refresh JWT (default 24 h)."""
    return _create_token(
        subject_type, subject_id, TOKEN_TYPE_REFRESH, settings.JWT_REFRESH_TTL_SECONDS
    )


def _create_token(
    subject_type: str, subject_id: str, token_type: str, ttl_seconds: int
) -> str:
    secret = settings.JWT_SECRET_KEY
    if secret is None:
        raise ValueError("JWT_SECRET_KEY is not set")
    now = int(time.time())
    token_payload = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "token_type": token_type,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(
        token_payload,
        secret.get_secret_value(),
        algorithm="HS256",
    )


def verify_refresh_token(token: str) -> SubjectPayload | None:
    """Verify a refresh token and return SubjectPayload, or None if invalid."""
    return _verify_token(token, TOKEN_TYPE_REFRESH)


def verify_auth_token(token: str) -> SubjectPayload | None:
    """Verify an auth token and return SubjectPayload, or None if invalid."""
    return _verify_token(token, TOKEN_TYPE_AUTH)


def _verify_token(token: str, expected_token_type: str) -> SubjectPayload | None:
    secret = settings.JWT_SECRET_KEY
    if secret is None:
        return None
    try:
        token_payload = jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=["HS256"],
        )
        if token_payload.get("token_type") != expected_token_type:
            return None
        subject_type = token_payload.get("subject_type")
        subject_id = token_payload.get("subject_id")
        if not subject_type or not subject_id:
            return None
        return SubjectPayload(
            subject_type=str(subject_type), subject_id=str(subject_id)
        )
    except jwt.PyJWTError:
        return None
    except Exception as e:
        _logger.warning("JWT verification failed: %s", e, exc_info=True)
        return None
