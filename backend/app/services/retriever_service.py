"""Vector retriever service for RAG pipeline.

This module provides functionality to:
- Search Qdrant for semantically similar content chunks
- Apply similarity threshold filtering
- Return chunks with metadata and relevance scores

Requirements: 4.2
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.db.qdrant import QdrantDatabase, get_qdrant_db
from app.services.query_processor import (
    QueryProcessor,
    ProcessedQuery,
    get_query_processor,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved content chunk with metadata and score."""

    id: str
    content: str
    chapter_id: str
    title: str
    section_title: str
    page_url: str
    position: int
    score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "chapter_id": self.chapter_id,
            "title": self.title,
            "section_title": self.section_title,
            "page_url": self.page_url,
            "position": self.position,
            "score": self.score,
        }


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""

    query: str
    processed_query: str
    chunks: list[RetrievedChunk]
    total_found: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "processed_query": self.processed_query,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "total_found": self.total_found,
        }


class VectorRetriever:
    """Service for retrieving relevant content chunks from Qdrant."""

    # Default retrieval parameters
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.5  # Lowered from 0.7 for better recall
    MAX_TOP_K = 20

    def __init__(
        self,
        qdrant_db: QdrantDatabase | None = None,
        query_processor: QueryProcessor | None = None,
        default_top_k: int = DEFAULT_TOP_K,
        default_score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ):
        """Initialize vector retriever.

        Args:
            qdrant_db: Qdrant database instance. Uses global if not provided.
            query_processor: Query processor instance. Uses global if not provided.
            default_top_k: Default number of results to return.
            default_score_threshold: Default minimum similarity score.
        """
        self._qdrant_db = qdrant_db
        self._query_processor = query_processor
        self.default_top_k = default_top_k
        self.default_score_threshold = default_score_threshold

    @property
    def qdrant_db(self) -> QdrantDatabase:
        """Get Qdrant database instance."""
        if self._qdrant_db is None:
            self._qdrant_db = get_qdrant_db()
        return self._qdrant_db

    @property
    def query_processor(self) -> QueryProcessor:
        """Get query processor instance."""
        if self._query_processor is None:
            self._query_processor = get_query_processor()
        return self._query_processor

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> RetrievalResult:
        """Retrieve relevant content chunks for a query.

        Args:
            query: User query string.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score threshold.

        Returns:
            RetrievalResult with matching chunks and metadata.
        """
        # Use defaults if not specified
        top_k = min(top_k or self.default_top_k, self.MAX_TOP_K)
        score_threshold = score_threshold or self.default_score_threshold

        logger.debug(
            f"Retrieving for query: {query[:100]}... "
            f"(top_k={top_k}, threshold={score_threshold})"
        )

        # Process the query to get embedding
        processed_query = await self.query_processor.process_query(query)

        # Search Qdrant
        search_results = await self.qdrant_db.search(
            query_vector=processed_query.embedding,
            limit=top_k,
            score_threshold=score_threshold,
        )

        # Convert to RetrievedChunk objects
        chunks = []
        for result in search_results:
            payload = result.get("payload", {})
            chunk = RetrievedChunk(
                id=str(result["id"]),
                content=payload.get("content", ""),
                chapter_id=payload.get("chapter_id", ""),
                title=payload.get("title", ""),
                section_title=payload.get("section_title", ""),
                page_url=payload.get("page_url", ""),
                position=payload.get("position", 0),
                score=result["score"],
            )
            chunks.append(chunk)

        logger.info(
            f"Retrieved {len(chunks)} chunks for query "
            f"(scores: {[f'{c.score:.3f}' for c in chunks]})"
        )

        return RetrievalResult(
            query=query,
            processed_query=processed_query.processed_query,
            chunks=chunks,
            total_found=len(chunks),
        )

    async def retrieve_with_embedding(
        self,
        embedding: list[float],
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve chunks using a pre-computed embedding.

        Args:
            embedding: Pre-computed query embedding vector.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of RetrievedChunk objects.
        """
        top_k = min(top_k or self.default_top_k, self.MAX_TOP_K)
        score_threshold = score_threshold or self.default_score_threshold

        search_results = await self.qdrant_db.search(
            query_vector=embedding,
            limit=top_k,
            score_threshold=score_threshold,
        )

        chunks = []
        for result in search_results:
            payload = result.get("payload", {})
            chunk = RetrievedChunk(
                id=str(result["id"]),
                content=payload.get("content", ""),
                chapter_id=payload.get("chapter_id", ""),
                title=payload.get("title", ""),
                section_title=payload.get("section_title", ""),
                page_url=payload.get("page_url", ""),
                position=payload.get("position", 0),
                score=result["score"],
            )
            chunks.append(chunk)

        return chunks

    async def retrieve_by_chapter(
        self,
        query: str,
        chapter_id: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> RetrievalResult:
        """Retrieve chunks from a specific chapter.

        Args:
            query: User query string.
            chapter_id: Chapter ID to filter by.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score threshold.

        Returns:
            RetrievalResult with matching chunks from the specified chapter.
        """
        # Get all results first
        result = await self.retrieve(
            query=query,
            top_k=(top_k or self.default_top_k) * 3,  # Get more to filter
            score_threshold=score_threshold,
        )

        # Filter by chapter
        filtered_chunks = [
            chunk for chunk in result.chunks
            if chunk.chapter_id == chapter_id
        ]

        # Limit to requested top_k
        top_k = top_k or self.default_top_k
        filtered_chunks = filtered_chunks[:top_k]

        return RetrievalResult(
            query=result.query,
            processed_query=result.processed_query,
            chunks=filtered_chunks,
            total_found=len(filtered_chunks),
        )


# Global retriever instance
_retriever: VectorRetriever | None = None


def get_retriever() -> VectorRetriever:
    """Get the global vector retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever
