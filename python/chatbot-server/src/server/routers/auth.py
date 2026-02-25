"""Auth API router (signup, login, user management)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Path

from src.auth.ports.auth_port import AuthPort
from src.auth.ports.types import AuthUser
from src.auth.utils.jwt import (
    SubjectType,
    create_auth_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.server.dependencies import get_auth
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

# UUID-v4 pattern for user_id path params (RFC 4122, lowercase hex)
_USER_ID_PATH = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


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


def _user_to_tokens_response(user: AuthUser) -> AuthTokensResponse:
    return AuthTokensResponse(
        user=_user_to_response(user),
        auth_token=create_auth_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/signup", response_model=AuthTokensResponse)
async def signup(
    body: SignupRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthTokensResponse:
    """Create a new user account. Returns user, auth JWT and refresh JWT."""
    auth = _require_auth(auth)
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
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthTokensResponse)
async def login(
    body: LoginRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthTokensResponse:
    """Verify credentials and return user with auth JWT and refresh JWT.

    Passwords with fewer than 8 characters are rejected without verification
    (consistent with signup min length).
    """
    auth = _require_auth(auth)
    user = await auth.verify_credentials(email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _user_to_tokens_response(user)


@router.post("/refresh", response_model=AuthTokensResponse)
async def refresh(
    body: RefreshRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthTokensResponse:
    """Exchange a valid refresh token for a new auth token and refresh token."""
    auth = _require_auth(auth)
    subject = verify_refresh_token(body.refresh_token)
    if subject is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    match subject.subject_type:
        case SubjectType.USER:
            user = await auth.get_user_by_id(subject.subject_id)
            if user is None:
                raise HTTPException(status_code=401, detail="User no longer exists")
            return _user_to_tokens_response(user)
        case SubjectType.SERVICE_ACCOUNT:
            raise HTTPException(
                status_code=501,
                detail="Service account refresh not implemented",
            )


@router.get("/users/{user_id}", response_model=AuthUserResponse)
async def get_user(
    user_id: str = _USER_ID_PATH,
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
    user_id: str = _USER_ID_PATH,
    body: UpdateUsernameRequest = Body(),
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
    user_id: str = _USER_ID_PATH,
    body: UpdatePasswordRequest = Body(),
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
    user_id: str = _USER_ID_PATH,
    auth: AuthPort | None = Depends(get_auth),
) -> dict:
    """Delete a user account."""
    auth = _require_auth(auth)
    ok = await auth.delete_account(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}
