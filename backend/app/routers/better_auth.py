"""Better Auth compatible endpoints.

Provides Better Auth-compatible API endpoints that work with the Better Auth client library.
These endpoints wrap our existing authentication service to maintain compatibility.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.auth_service import (
    AuthResponse,
    AuthService,
    UserCreate,
    UserLogin,
    get_auth_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["better-auth"])


class BetterAuthSignUpRequest(BaseModel):
    """Better Auth sign-up request schema."""
    email: str
    password: str
    name: str
    software_experience: str | None = None
    hardware_experience: str | None = None
    programming_languages: list[str] | None = None
    robotics_experience: bool | None = None
    ai_experience: bool | None = None


class BetterAuthSignInRequest(BaseModel):
    """Better Auth sign-in request schema."""
    email: str
    password: str


class BetterAuthUser(BaseModel):
    """Better Auth user response schema."""
    id: str
    email: str
    name: str
    emailVerified: bool
    createdAt: str
    updatedAt: str
    software_experience: str | None = None
    hardware_experience: str | None = None
    programming_languages: list[str] | None = None
    robotics_experience: bool | None = None
    ai_experience: bool | None = None


class BetterAuthSession(BaseModel):
    """Better Auth session response schema."""
    token: str
    expiresAt: str


class BetterAuthSignUpResponse(BaseModel):
    """Better Auth sign-up response schema."""
    user: BetterAuthUser
    session: BetterAuthSession | None = None
    token: str


class BetterAuthSignInResponse(BaseModel):
    """Better Auth sign-in response schema."""
    user: BetterAuthUser
    session: BetterAuthSession | None = None
    token: str


@router.post(
    "/sign-up/email",
    response_model=BetterAuthSignUpResponse,
    status_code=status.HTTP_201_CREATED,
)
async def better_auth_sign_up(
    request: BetterAuthSignUpRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> BetterAuthSignUpResponse:
    """Better Auth compatible sign-up endpoint.

    This endpoint provides Better Auth compatibility while using our existing
    authentication service.
    """
    # Convert Better Auth request to our UserCreate format
    user_data = UserCreate(
        email=request.email,
        password=request.password,
        background={
            "software_experience": request.software_experience or "beginner",
            "hardware_experience": request.hardware_experience or "beginner",
            "programming_languages": request.programming_languages or [],
            "robotics_experience": request.robotics_experience or False,
            "ai_experience": request.ai_experience or False,
        },
    )

    result = await auth_service.register_user(user_data)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again.",
        )

    # Convert our response to Better Auth format
    return BetterAuthSignUpResponse(
        user=BetterAuthUser(
            id=result.user.id,
            email=result.user.email,
            name=request.name,
            emailVerified=False,
            createdAt=result.user.created_at,
            updatedAt=result.user.created_at,
            software_experience=result.user.software_experience,
            hardware_experience=result.user.hardware_experience,
            programming_languages=result.user.programming_languages,
            robotics_experience=result.user.robotics_experience,
            ai_experience=result.user.ai_experience,
        ),
        session=BetterAuthSession(
            token=result.token.access_token,
            expiresAt=result.token.expires_at,
        ),
        token=result.token.access_token,
    )


@router.post(
    "/sign-in/email",
    response_model=BetterAuthSignInResponse,
)
async def better_auth_sign_in(
    request: BetterAuthSignInRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> BetterAuthSignInResponse:
    """Better Auth compatible sign-in endpoint.

    This endpoint provides Better Auth compatibility while using our existing
    authentication service.
    """
    # Convert Better Auth request to our UserLogin format
    credentials = UserLogin(
        email=request.email,
        password=request.password,
    )

    result = await auth_service.login_user(credentials)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert our response to Better Auth format
    return BetterAuthSignInResponse(
        user=BetterAuthUser(
            id=result.user.id,
            email=result.user.email,
            name=request.email.split("@")[0],  # Use email prefix as name
            emailVerified=False,
            createdAt=result.user.created_at,
            updatedAt=result.user.created_at,
            software_experience=result.user.software_experience,
            hardware_experience=result.user.hardware_experience,
            programming_languages=result.user.programming_languages,
            robotics_experience=result.user.robotics_experience,
            ai_experience=result.user.ai_experience,
        ),
        session=BetterAuthSession(
            token=result.token.access_token,
            expiresAt=result.token.expires_at,
        ),
        token=result.token.access_token,
    )
