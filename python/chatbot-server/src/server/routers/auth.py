"""Auth API router (signup, login)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.auth.ports.auth_port import AuthPort
from src.server.dependencies import get_auth
from src.server.schemas.auth import AuthUserResponse, LoginRequest, SignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _require_auth(auth: AuthPort | None) -> AuthPort:
    if auth is None:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured. Set AUTH_ENABLED=true and provider config.",
        )
    return auth


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
        return AuthUserResponse(id=user.id, email=user.email, username=user.username)
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthUserResponse)
async def login(
    body: LoginRequest,
    auth: AuthPort | None = Depends(get_auth),
) -> AuthUserResponse:
    """Verify credentials and return user info."""
    auth = _require_auth(auth)
    user = await auth.verify_credentials(email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthUserResponse(id=user.id, email=user.email, username=user.username)
