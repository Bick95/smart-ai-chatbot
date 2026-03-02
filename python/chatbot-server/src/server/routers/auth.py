"""Auth API router (signup, login, user management)."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Body, Depends, HTTPException, Path

from src.settings import settings

from src.auth.ports.auth_port import AuthPort
from src.auth.ports.types import AuthUser
from src.auth.utils.jwt import (
    SubjectPayload,
    SubjectType,
    create_auth_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.server.dependencies import get_auth, get_current_subject
from src.utils.logging import get_logger
from src.server.schemas.auth import (
    AuthTokensResponse,
    AuthUserResponse,
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    UpdatePasswordRequest,
    UpdateUsernameRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])
_logger = get_logger(__name__)

# UUID-v4 pattern for user_id path params (RFC 4122, lowercase hex)
_USER_ID_PATH = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _user_to_response(user: AuthUser) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id, email=user.email, username=user.username, created_at=user.created_at
    )


def _user_to_tokens_response(
    user: AuthUser,
    *,
    subject: SubjectPayload | None = None,
) -> AuthTokensResponse:
    if subject is not None and subject.subject_id != user.id:
        raise ValueError(
            f"subject.subject_id ({subject.subject_id!r}) does not match user.id ({user.id!r})"
        )
    sub = subject or SubjectPayload(subject_type=SubjectType.USER, subject_id=user.id)
    return AuthTokensResponse(
        user=_user_to_response(user),
        auth_token=create_auth_token(sub),
        refresh_token=create_refresh_token(sub),
    )


@router.post("/signup", response_model=AuthTokensResponse)
async def signup(
    body: SignupRequest,
    auth: AuthPort = Depends(get_auth),
) -> AuthTokensResponse:
    """Create a new user account. Returns user, auth JWT and refresh JWT."""
    if settings.SIGNUP_INVITE_KEY is not None:
        expected = settings.SIGNUP_INVITE_KEY.get_secret_value()
        if body.invite_key is None or not secrets.compare_digest(
            body.invite_key, expected
        ):
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing invite key",
            )
    try:
        user = await auth.signup(
            email=body.email,
            username=body.username,
            password=body.password,
        )
        return _user_to_tokens_response(user)
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        _logger.warning("signup: unexpected %s", type(e).__name__, exc_info=True)
        # Never expose internal error details to clients
        raise HTTPException(status_code=400, detail="Registration failed")


@router.post("/login", response_model=AuthTokensResponse)
async def login(
    body: LoginRequest,
    auth: AuthPort = Depends(get_auth),
) -> AuthTokensResponse:
    """Verify credentials and return user with auth JWT and refresh JWT.

    Passwords with fewer than 8 characters are rejected without verification
    (consistent with signup min length).
    """
    user = await auth.verify_credentials(email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _user_to_tokens_response(user)


@router.post("/refresh", response_model=AuthTokensResponse)
async def refresh(
    body: RefreshRequest,
    auth: AuthPort = Depends(get_auth),
) -> AuthTokensResponse:
    """Exchange a valid refresh token for a new auth token and refresh token."""
    subject = verify_refresh_token(body.refresh_token)
    if subject is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    match subject.subject_type:
        case SubjectType.USER:
            user = await auth.get_user_by_id(subject.subject_id)
            if user is None:
                raise HTTPException(status_code=401, detail="User no longer exists")
            return _user_to_tokens_response(user, subject=subject)
        case SubjectType.SERVICE_ACCOUNT:
            raise HTTPException(
                status_code=501,
                detail="Service account refresh not implemented",
            )


def _require_own_user(subject: SubjectPayload, user_id: str) -> None:
    """Raise 403 if subject cannot access the given user_id."""
    if subject.subject_type != SubjectType.USER or subject.subject_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/users/{user_id}", response_model=AuthUserResponse)
async def get_user(
    user_id: str = _USER_ID_PATH,
    auth: AuthPort = Depends(get_auth),
    subject: SubjectPayload = Depends(get_current_subject),
) -> AuthUserResponse:
    """Get a user by ID. Requires auth; users can only access their own data."""
    _require_own_user(subject, user_id)
    user = await auth.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.patch("/users/{user_id}/username", response_model=AuthUserResponse)
async def update_username(
    user_id: str = _USER_ID_PATH,
    body: UpdateUsernameRequest = Body(),
    auth: AuthPort = Depends(get_auth),
    subject: SubjectPayload = Depends(get_current_subject),
) -> AuthUserResponse:
    """Update a user's username. Requires auth; users can only update their own."""
    _require_own_user(subject, user_id)
    ok = await auth.update_username(user_id, body.username)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    user = await auth.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.patch("/users/{user_id}/password")
async def update_password(
    user_id: str = _USER_ID_PATH,
    body: UpdatePasswordRequest = Body(),
    auth: AuthPort = Depends(get_auth),
    subject: SubjectPayload = Depends(get_current_subject),
) -> dict:
    """Update a user's password. Requires auth; users can only update their own."""
    _require_own_user(subject, user_id)
    ok = await auth.update_password(user_id, body.password)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str = _USER_ID_PATH,
    auth: AuthPort = Depends(get_auth),
    subject: SubjectPayload = Depends(get_current_subject),
) -> dict:
    """Delete a user account. Requires auth; users can only delete their own."""
    _require_own_user(subject, user_id)
    ok = await auth.delete_account(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}
