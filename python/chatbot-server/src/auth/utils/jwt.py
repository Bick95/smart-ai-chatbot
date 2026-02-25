"""JWT creation and verification for auth and refresh tokens."""

from __future__ import annotations

import time

import jwt

from src.settings import settings

TOKEN_TYPE_AUTH = "auth"
TOKEN_TYPE_REFRESH = "refresh"


def create_auth_token(user_id: str) -> str:
    """Create a short-lived auth JWT (default 15 min)."""
    return _create_token(user_id, TOKEN_TYPE_AUTH, settings.JWT_AUTH_TTL_SECONDS)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh JWT (default 24 h)."""
    return _create_token(user_id, TOKEN_TYPE_REFRESH, settings.JWT_REFRESH_TTL_SECONDS)


def _create_token(user_id: str, token_type: str, ttl_seconds: int) -> str:
    secret = settings.JWT_SECRET_KEY
    if secret is None:
        raise ValueError("JWT_SECRET_KEY is not set")
    now = int(time.time())
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(
        payload,
        secret.get_secret_value(),
        algorithm="HS256",
    )


def verify_refresh_token(token: str) -> str | None:
    """Verify a refresh token and return user_id, or None if invalid."""
    return _verify_token(token, TOKEN_TYPE_REFRESH)


def verify_auth_token(token: str) -> str | None:
    """Verify an auth token and return user_id, or None if invalid."""
    return _verify_token(token, TOKEN_TYPE_AUTH)


def _verify_token(token: str, expected_type: str) -> str | None:
    secret = settings.JWT_SECRET_KEY
    if secret is None:
        return None
    try:
        payload = jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=["HS256"],
        )
        if payload.get("type") != expected_type:
            return None
        user_id = payload.get("sub")
        return str(user_id) if user_id else None
    except jwt.PyJWTError:
        return None
