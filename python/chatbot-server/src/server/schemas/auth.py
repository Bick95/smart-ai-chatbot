"""Auth request/response schemas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.settings import settings

# Restrict to safe characters to prevent injection; allow only valid email/username formats
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_username(v: str) -> str:
    if not USERNAME_PATTERN.fullmatch(v):
        raise ValueError(
            "Username must contain only letters, numbers, underscores, and hyphens"
        )
    return v


def _validate_email(v: str) -> str:
    if not EMAIL_PATTERN.fullmatch(v):
        raise ValueError("Invalid email format")
    return v


class SignupRequest(BaseModel):
    """Request body for signup.

    invite_key is required when SIGNUP_INVITE_KEY is set in settings.
    """

    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)

    _email = field_validator("email")(_validate_email)
    _username = field_validator("username")(_validate_username)
    password: str = Field(..., min_length=8, max_length=128)
    invite_key: str | None = Field(
        default=None,
        description="Required when SIGNUP_INVITE_KEY is set; must match the configured key",
    )


class LoginRequest(BaseModel):
    """Request body for login.

    Password min_length=8 matches SignupRequest; reject short passwords
    without attempting verification.
    """

    email: str = Field(..., min_length=5, max_length=255)

    _email = field_validator("email")(_validate_email)
    password: str = Field(..., min_length=8, max_length=128)


class AuthUserResponse(BaseModel):
    """User info in auth responses."""

    id: str
    email: str
    username: str
    created_at: datetime | None = None


def _auth_token_ttl_description() -> str:
    mins = settings.JWT_AUTH_TTL_SECONDS // 60
    return f"Short-lived JWT for API auth ({mins} min)"


def _refresh_token_ttl_description() -> str:
    hours = settings.JWT_REFRESH_TTL_SECONDS // 3600
    return f"Long-lived JWT to obtain new auth tokens ({hours} h)"


class AuthTokensResponse(BaseModel):
    """Signup/login response with user and JWTs."""

    user: AuthUserResponse
    auth_token: str = Field(..., description=_auth_token_ttl_description())
    refresh_token: str = Field(..., description=_refresh_token_ttl_description())


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str = Field(..., min_length=1)


class UpdateUsernameRequest(BaseModel):
    """Request body for updating username."""

    username: str = Field(..., min_length=1, max_length=255)

    _username = field_validator("username")(_validate_username)


class UpdateEmailRequest(BaseModel):
    """Request body for updating email."""

    email: str = Field(..., min_length=5, max_length=255)

    _email = field_validator("email")(_validate_email)


class UpdatePasswordRequest(BaseModel):
    """Request body for updating password."""

    password: str = Field(..., min_length=8, max_length=128)
