"""Auth API router (signup, login, user management)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.auth.ports.auth_port import AuthPort
from src.auth.ports.types import AuthUser
from src.server.dependencies import get_auth
from src.server.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    SignupRequest,
    UpdatePasswordRequest,
    UpdateUsernameRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _require_auth(auth: AuthPort | None) -> AuthPort:
    if auth is None:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured. Set AUTH_ENABLED=true and provider config.",
        )
    return auth


def _user_to_response(user: AuthUser) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id, email=user.email, username=user.username, created_at=user.created_at
    )


@router.post("/signup", response_model=AuthUserResponse)
async def signup(
    body: SignupRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthUserResponse:
    """Create a new user account."""
    auth = _require_auth(auth)
    try:
        user = await auth.signup(
            email=body.email,
            username=body.username,
            password=body.password,
        )
        return _user_to_response(user)
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthUserResponse)
async def login(
    body: LoginRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthUserResponse:
    """Verify credentials and return user info.

    Passwords with fewer than 8 characters are rejected without verification
    (consistent with signup min length).
    """
    auth = _require_auth(auth)
    user = await auth.verify_credentials(email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _user_to_response(user)


@router.get("/users/{user_id}", response_model=AuthUserResponse)
async def get_user(
    user_id: str,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthUserResponse:
    """Get a user by ID."""
    auth = _require_auth(auth)
    user = await auth.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.patch("/users/{user_id}/username", response_model=AuthUserResponse)
async def update_username(
    user_id: str,
    body: UpdateUsernameRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthUserResponse:
    """Update a user's username."""
    auth = _require_auth(auth)
    ok = await auth.update_username(user_id, body.username)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    user = await auth.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.patch("/users/{user_id}/password")
async def update_password(
    user_id: str,
    body: UpdatePasswordRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> dict:
    """Update a user's password."""
    auth = _require_auth(auth)
    ok = await auth.update_password(user_id, body.password)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    auth: AuthPort | None = Depends(get_auth),
) -> dict:
    """Delete a user account."""
    auth = _require_auth(auth)
    ok = await auth.delete_account(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}
