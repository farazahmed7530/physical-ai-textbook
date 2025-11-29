"""Chat API endpoints.

This module implements the POST /api/chat endpoint that:
- Validates input with Pydantic
- Integrates with the RAG pipeline
- Stores chat history in PostgreSQL

Requirements: 5.1, 5.2
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag_service import RAGService, RAGRequest, get_rag_service
from app.db.postgres import get_postgres_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model with validation.

    Attributes:
        query: The user's question (required, non-empty).
        selected_text: Optional text selected by the user for context.
        user_id: Optional user ID for authenticated users.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The user's question about the textbook content",
    )
    selected_text: str | None = Field(
        default=None,
        max_length=10000,
        description="Optional text selected by the user for additional context",
    )
    user_id: str | None = Field(
        default=None,
        description="Optional user ID for authenticated users",
    )

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate that query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

    @field_validator("selected_text")
    @classmethod
    def selected_text_strip(cls, v: str | None) -> str | None:
        """Strip whitespace from selected text if provided."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str | None) -> str | None:
        """Validate user_id is a valid UUID if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("user_id must be a valid UUID")
        return v


class Source(BaseModel):
    """Source citation model."""

    chapter_id: str = Field(..., description="The chapter ID where the content was found")
    section_title: str = Field(..., description="The section title within the chapter")
    page_url: str = Field(..., description="URL to the source page")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")


class ChatResponse(BaseModel):
    """Chat response model.

    Attributes:
        response: The generated response text.
        sources: List of source citations.
        is_fallback: Whether this is a fallback response (no relevant content found).
    """

    response: str = Field(..., description="The generated response text")
    sources: list[Source] = Field(default_factory=list, description="Source citations")
    is_fallback: bool = Field(default=False, description="Whether this is a fallback response")


async def get_db_session():
    """Dependency to get database session."""
    try:
        db = get_postgres_db()
        async for session in db.get_session():
            yield session
    except RuntimeError:
        # Database not initialized - yield None
        yield None


async def store_chat_message(
    session: AsyncSession | None,
    query: str,
    response: str,
    sources: list[dict[str, Any]],
    selected_text: str | None,
    user_id: str | None,
) -> None:
    """Store chat message in PostgreSQL.

    Args:
        session: Database session (may be None if DB not configured).
        query: The user's query.
        response: The generated response.
        sources: List of source citations.
        selected_text: Optional selected text context.
        user_id: Optional user ID.
    """
    if session is None:
        logger.debug("Database session not available, skipping chat history storage")
        return

    try:
        # Import here to avoid circular imports
        from app.models.chat import ChatMessage

        # Convert user_id string to UUID if provided
        user_uuid = uuid.UUID(user_id) if user_id else None

        chat_message = ChatMessage(
            user_id=user_uuid,
            query=query,
            response=response,
            sources=sources,
            selected_text=selected_text,
        )

        session.add(chat_message)
        await session.commit()
        logger.info(f"Stored chat message with ID: {chat_message.id}")
    except Exception as e:
        logger.error(f"Failed to store chat message: {e}")
        # Don't raise - chat history storage failure shouldn't break the chat
        await session.rollback()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> ChatResponse:
    """Process a chat request and return a response with sources.

    This endpoint:
    1. Validates the input request
    2. Processes the query through the RAG pipeline
    3. Stores the chat message in PostgreSQL (if configured)
    4. Returns the response with source citations

    Args:
        request: The chat request with query and optional context.
        rag_service: The RAG service for processing queries.
        db_session: Optional database session for storing chat history.

    Returns:
        ChatResponse with the generated response and source citations.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    logger.info(f"Processing chat request: query='{request.query[:50]}...'")

    try:
        # Create RAG request
        rag_request = RAGRequest(
            query=request.query,
            selected_text=request.selected_text,
            user_id=request.user_id,
        )

        # Process through RAG pipeline
        rag_response = await rag_service.process_query(rag_request)

        # Convert sources to response format
        sources = [
            Source(
                chapter_id=s.get("chapter_id", "unknown"),
                section_title=s.get("section_title", "Unknown Section"),
                page_url=s.get("page_url", ""),
                relevance_score=s.get("relevance_score", 0.0),
            )
            for s in rag_response.sources
        ]

        # Store chat message in database (async, non-blocking on failure)
        await store_chat_message(
            session=db_session,
            query=request.query,
            response=rag_response.response,
            sources=rag_response.sources,
            selected_text=request.selected_text,
            user_id=request.user_id,
        )

        return ChatResponse(
            response=rag_response.response,
            sources=sources,
            is_fallback=rag_response.is_fallback,
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again.",
        )
