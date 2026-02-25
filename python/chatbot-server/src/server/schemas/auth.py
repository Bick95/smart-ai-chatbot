"""Auth request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Request body for signup."""

    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request body for login.

    Password min_length=8 matches SignupRequest; reject short passwords
    without attempting verification.
    """

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class AuthUserResponse(BaseModel):
    """User info in auth responses."""

    id: str
    email: str
    username: str
    created_at: datetime | None = None


class UpdateUsernameRequest(BaseModel):
    """Request body for updating username."""

    username: str = Field(..., min_length=1, max_length=255)


class UpdatePasswordRequest(BaseModel):
    """Request body for updating password."""

    password: str = Field(..., min_length=8, max_length=128)
