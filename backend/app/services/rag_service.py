"""RAG (Retrieval-Augmented Generation) service.

This module provides the main RAG pipeline that:
- Retrieves relevant content from the vector database
- Builds context from retrieved chunks
- Generates responses with citations
- Handles fallback for no relevant results

Requirements: 3.1, 3.2, 3.3, 3.5
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.services.retriever_service import VectorRetriever, get_retriever
from app.services.response_generator import (
    ResponseGenerator,
    GeneratedResponse,
    get_response_generator,
)

logger = logging.getLogger(__name__)


@dataclass
class RAGRequest:
    """Request for RAG pipeline."""

    query: str
    selected_text: str | None = None
    user_id: str | None = None
    top_k: int = 5
    score_threshold: float = 0.5  # Lowered from 0.7 for better recall


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""

    response: str
    sources: list[dict[str, Any]]
    is_fallback: bool
    query: str
    selected_text: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "response": self.response,
            "sources": self.sources,
            "is_fallback": self.is_fallback,
            "query": self.query,
            "selected_text": self.selected_text,
        }


class RAGService:
    """Main RAG service that orchestrates retrieval and generation."""

    def __init__(
        self,
        retriever: VectorRetriever | None = None,
        response_generator: ResponseGenerator | None = None,
    ):
        """Initialize RAG service.

        Args:
            retriever: Vector retriever instance.
            response_generator: Response generator instance.
        """
        self._retriever = retriever
        self._response_generator = response_generator

    @property
    def retriever(self) -> VectorRetriever:
        """Get retriever instance."""
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    @property
    def response_generator(self) -> ResponseGenerator:
        """Get response generator instance."""
        if self._response_generator is None:
            self._response_generator = get_response_generator()
        return self._response_generator

    async def process_query(self, request: RAGRequest) -> RAGResponse:
        """Process a RAG query.

        Args:
            request: RAG request with query and options.

        Returns:
            RAGResponse with generated answer and sources.
        """
        logger.info(f"Processing RAG query: {request.query[:100]}...")

        # Step 1: Retrieve relevant chunks
        retrieval_result = await self.retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
        )

        logger.debug(
            f"Retrieved {len(retrieval_result.chunks)} chunks "
            f"for query: {request.query[:50]}..."
        )

        # Step 2: Generate response
        generated = await self.response_generator.generate_response(
            query=request.query,
            retrieval_result=retrieval_result,
            selected_text=request.selected_text,
        )

        # Convert to RAGResponse
        return RAGResponse(
            response=generated.response,
            sources=[s.to_dict() for s in generated.sources],
            is_fallback=generated.is_fallback,
            query=request.query,
            selected_text=request.selected_text,
        )


# Global RAG service instance
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
