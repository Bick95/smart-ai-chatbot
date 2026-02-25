"""JWT creation and verification for auth and refresh tokens."""

from __future__ import annotations

import time
from enum import Enum

import jwt
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from src.auth.utils.validation import is_valid_uuid4, validate_uuid4
from src.settings import settings
from src.utils.logging import get_logger

_logger = get_logger(__name__)

TOKEN_TYPE_AUTH = "auth"
TOKEN_TYPE_REFRESH = "refresh"


class SubjectType(str, Enum):
    """Valid subject types for authentication."""

    USER = "user"
    SERVICE_ACCOUNT = "service_account"


class SubjectPayload(BaseModel):
    """Subject claim extracted from a decoded token (who can act on the system).

    All validations run when creating from raw token data via model_validate.
    subject_type must be a valid SubjectType. subject_id must be UUID-v4.
    """

    model_config = ConfigDict(frozen=True)

    subject_type: SubjectType
    subject_id: str

    @model_validator(mode="before")
    @classmethod
    def extract_subject_claims(cls, data: object) -> dict:
        """Extract and normalize subject claims from raw token payload."""
        if not isinstance(data, dict):
            return data
        subject_type = data.get("subject_type")
        subject_id = data.get("subject_id")
        if subject_type is None or subject_id is None:
            raise ValueError("subject_type and subject_id are required")
        return {"subject_type": subject_type, "subject_id": str(subject_id)}

    @field_validator("subject_id")
    @classmethod
    def subject_id_must_be_uuid4(cls, v: str) -> str:
        if not is_valid_uuid4(v):
            raise ValueError(f"subject_id must be UUID-v4, got {v!r}")
        return v


def create_auth_token(
    subject_id: str,
    *,
    subject_type: SubjectType = SubjectType.USER,
) -> str:
    """Create a short-lived auth JWT (default 15 min)."""
    return _create_token(
        subject_type.value, subject_id, TOKEN_TYPE_AUTH, settings.JWT_AUTH_TTL_SECONDS
    )


def create_refresh_token(
    subject_id: str,
    *,
    subject_type: SubjectType = SubjectType.USER,
) -> str:
    """Create a long-lived refresh JWT (default 24 h)."""
    return _create_token(
        subject_type.value, subject_id, TOKEN_TYPE_REFRESH, settings.JWT_REFRESH_TTL_SECONDS
    )


def _create_token(
    subject_type: str, subject_id: str, token_type: str, ttl_seconds: int
) -> str:
    validate_uuid4(subject_id)
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
        try:
            return SubjectPayload.model_validate(token_payload)
        except ValidationError:
            return None
    except (jwt.PyJWTError, ValueError):
        return None
    except Exception as e:
        _logger.warning("JWT verification failed: %s", e, exc_info=True)
        return None
