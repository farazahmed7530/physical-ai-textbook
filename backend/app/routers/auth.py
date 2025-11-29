"""Authentication API endpoints.

Implements user registration, login, and logout endpoints.
Requirements: 6.1, 6.2, 6.3, 6.4
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.services.auth_service import (
    AuthResponse,
    AuthService,
    UserCreate,
    UserLogin,
    UserResponse,
    get_auth_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LogoutRequest(BaseModel):
    """Request schema for logout."""
    token: str


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    type: str


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Registration failed"},
    },
)
async def register(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Register a new user with background information.

    Requirements: 6.1, 6.5

    - Collects email, password, and background information
    - Hashes password securely using bcrypt
    - Stores user data in PostgreSQL
    - Returns user info and session token
    """
    result = await auth_service.register_user(user_data)

    if not result:
        # Security: Generic error message (Requirement 6.4)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again.",
        )

    return result


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def login(
    credentials: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Authenticate user and create session.

    Requirements: 6.2, 6.4

    - Validates credentials against stored user data
    - Issues JWT session token on success
    - Returns generic error on failure (security)
    """
    result = await auth_service.login_user(credentials)

    if not result:
        # Security: Generic error message that doesn't reveal if email exists
        # Requirement 6.4
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid token"},
    },
)
async def logout(
    logout_request: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutResponse:
    """Invalidate a session token.

    Requirements: 6.3

    - Removes session from database
    - Token becomes invalid immediately
    """
    success = await auth_service.logout_user(logout_request.token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return LogoutResponse(success=True, message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> UserResponse:
    """Get the current authenticated user.

    Requirements: 6.2

    - Validates the Bearer token from Authorization header
    - Returns user information if valid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")
    user = await auth_service.validate_session(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> Optional[UserResponse]:
    """Get the current user if authenticated, None otherwise.

    Useful for endpoints that work with or without authentication.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    return await auth_service.validate_session(token)


async def require_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> UserResponse:
    """Dependency that requires authentication.

    Use this as a dependency for protected endpoints.
    """
    user = await get_optional_current_user(authorization, auth_service)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
