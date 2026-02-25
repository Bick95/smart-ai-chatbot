"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Request body for signup."""

    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request body for login."""

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class AuthUserResponse(BaseModel):
    """User info in auth responses."""

    id: str
    email: str
    username: str
