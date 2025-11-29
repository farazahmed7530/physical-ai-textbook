"""Translation API endpoints.

Implements content translation to Urdu.
Requirements: 8.1, 8.2, 8.3, 8.4
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.services.auth_service import AuthService, UserResponse, get_auth_service
from app.services.translation_service import (
    TranslationService,
    TranslationRequest,
    TranslationResponse,
    get_translation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translate", tags=["translation"])


class TranslateRequest(BaseModel):
    """Request schema for content translation."""
    chapter_id: str
    content: str


class RTLCSSResponse(BaseModel):
    """Response schema for RTL CSS styles."""
    css: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    type: str


async def get_optional_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> Optional[UserResponse]:
    """Dependency that optionally validates authentication.

    Translation can work for both authenticated and unauthenticated users,
    but we track the user if authenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    return await auth_service.validate_session(token)


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
    response_model=TranslationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Translation failed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def translate_content(
    request: TranslateRequest,
    current_user: Annotated[UserResponse, Depends(require_current_user)],
    translation_service: Annotated[
        TranslationService, Depends(get_translation_service)
    ],
) -> TranslationResponse:
    """Translate chapter content to Urdu.

    Requirements: 8.1, 8.2, 8.3, 8.4

    - Requires authentication
    - Translates content to Urdu using OpenAI
    - Preserves technical terms with transliteration
    - Applies RTL formatting
    - Caches translated content for subsequent visits
    """
    try:
        translation_request = TranslationRequest(
            chapter_id=request.chapter_id,
            content=request.content,
            language="ur",  # Default to Urdu
        )

        result = await translation_service.translate_content(translation_request)
        return result

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation failed. Please try again.",
        )


@router.get(
    "/css",
    response_model=RTLCSSResponse,
)
async def get_rtl_css(
    translation_service: Annotated[
        TranslationService, Depends(get_translation_service)
    ],
) -> RTLCSSResponse:
    """Get CSS styles for RTL content display.

    Requirements: 8.3

    - Returns CSS for proper RTL text direction
    - Handles mixed LTR/RTL content (code blocks)
    - Ensures proper text alignment
    """
    css = translation_service.get_rtl_css()
    return RTLCSSResponse(css=css)


@router.delete(
    "/cache/{chapter_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def invalidate_chapter_cache(
    chapter_id: str,
    current_user: Annotated[UserResponse, Depends(require_current_user)],
    translation_service: Annotated[
        TranslationService, Depends(get_translation_service)
    ],
) -> dict:
    """Invalidate cached translations for a chapter.

    Requirements: 8.4

    - Useful when chapter content is updated
    - Forces re-translation on next request
    """
    deleted_count = await translation_service.invalidate_chapter_cache(chapter_id)
    return {
        "success": True,
        "message": f"Invalidated {deleted_count} cached translations",
        "deleted_count": deleted_count,
    }
