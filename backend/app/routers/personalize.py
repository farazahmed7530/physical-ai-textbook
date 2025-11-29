"""Personalization API endpoints.

Implements content personalization based on user background.
Requirements: 7.1, 7.2, 7.3, 7.4
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.services.auth_service import AuthService, UserResponse, get_auth_service
from app.services.personalization_service import (
    PersonalizationService,
    PersonalizedContentRequest,
    PersonalizedContentResponse,
    get_personalization_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/personalize", tags=["personalization"])


class PersonalizeRequest(BaseModel):
    """Request schema for content personalization."""
    chapter_id: str
    content: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    type: str


async def require_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> UserResponse:
    """Dependency that requires authentication."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
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


@router.post(
    "",
    response_model=PersonalizedContentResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Personalization failed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"model": ErrorResponse, "description": "Incomplete profile"},
    },
)
async def personalize_content(
    request: PersonalizeRequest,
    current_user: Annotated[UserResponse, Depends(require_current_user)],
    personalization_service: Annotated[
        PersonalizationService, Depends(get_personalization_service)
    ],
) -> PersonalizedContentResponse:
    """Personalize chapter content based on user background.

    Requirements: 7.1, 7.2, 7.3, 7.4

    - Requires authentication
    - Analyzes user background to determine experience level
    - Adapts content complexity while preserving technical terms
    - Caches personalized content for subsequent visits
    - Returns error if user profile is incomplete (7.3)
    """
    try:
        personalized_request = PersonalizedContentRequest(
            chapter_id=request.chapter_id,
            user_id=current_user.id,
            original_content=request.content,
        )

        result = await personalization_service.personalize_content(personalized_request)
        return result

    except ValueError as e:
        error_message = str(e)
        # Check if it's an incomplete profile error (Requirement 7.3)
        if "incomplete" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    except Exception as e:
        logger.error(f"Personalization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Personalization failed. Please try again.",
        )


@router.delete(
    "/cache",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def invalidate_user_cache(
    current_user: Annotated[UserResponse, Depends(require_current_user)],
    personalization_service: Annotated[
        PersonalizationService, Depends(get_personalization_service)
    ],
) -> dict:
    """Invalidate all cached personalized content for the current user.

    Requirements: 7.4

    - Useful when user updates their profile
    - Forces re-personalization on next request
    """
    deleted_count = await personalization_service.invalidate_user_cache(current_user.id)
    return {
        "success": True,
        "message": f"Invalidated {deleted_count} cached entries",
        "deleted_count": deleted_count,
    }
