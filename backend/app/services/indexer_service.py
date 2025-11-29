"""Content indexing service for Qdrant vector database.

This module provides functionality to:
- Index content chunks with embeddings into Qdrant
- Handle upsert operations with metadata
- Support re-indexing for content updates

Requirements: 4.1, 4.3
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qdrant_client import models

from app.config import get_settings
from app.db.qdrant import get_qdrant_db, QdrantDatabase
from app.services.content_parser import (
    ContentChunk,
    parse_textbook_directory,
)
from app.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


@dataclass
class IndexingResult:
    """Result of an indexing operation."""

    total_chunks: int
    indexed_chunks: int
    failed_chunks: int
    chapters_processed: list[str]
    errors: list[str]


@dataclass
class IndexedChunk:
    """A chunk ready for indexing with its embedding."""

    id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any]


class QdrantIndexer:
    """Service for indexing content into Qdrant vector database."""

    # Batch size for upsert operations
    UPSERT_BATCH_SIZE = 100

    def __init__(
        self,
        qdrant_db: QdrantDatabase | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        """Initialize indexer with database and embedding service.

        Args:
            qdrant_db: Qdrant database instance. Uses global if not provided.
            embedding_service: Embedding service instance. Uses global if not provided.
        """
        self._qdrant_db = qdrant_db
        self._embedding_service = embedding_service

    @property
    def qdrant_db(self) -> QdrantDatabase:
        """Get Qdrant database instance."""
        if self._qdrant_db is None:
            self._qdrant_db = get_qdrant_db()
        return self._qdrant_db

    @property
    def embedding_service(self) -> EmbeddingService:
        """Get embedding service instance."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def index_chunks(
        self,
        chunks: list[ContentChunk],
    ) -> IndexingResult:
        """Index a list of content chunks into Qdrant.

        Args:
            chunks: List of content chunks to index.

        Returns:
            IndexingResult with statistics about the operation.
        """
        if not chunks:
            return IndexingResult(
                total_chunks=0,
                indexed_chunks=0,
                failed_chunks=0,
                chapters_processed=[],
                errors=[],
            )

        logger.info(f"Starting indexing of {len(chunks)} chunks")

        # Track chapters processed
        chapters = set()
        errors = []
        indexed_count = 0
        failed_count = 0

        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        try:
            embedding_results = await self.embedding_service.generate_embeddings(texts)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return IndexingResult(
                total_chunks=len(chunks),
                indexed_chunks=0,
                failed_chunks=len(chunks),
                chapters_processed=[],
                errors=[f"Embedding generation failed: {str(e)}"],
            )

        # Prepare indexed chunks with embeddings
        indexed_chunks = []
        for chunk, embedding_result in zip(chunks, embedding_results):
            chapters.add(chunk.metadata.chapter_id)
            indexed_chunks.append(
                IndexedChunk(
                    id=chunk.id,
                    content=chunk.content,
                    embedding=embedding_result.embedding,
                    metadata={
                        "chapter_id": chunk.metadata.chapter_id,
                        "title": chunk.metadata.title,
                        "section_title": chunk.metadata.section_title,
                        "page_url": chunk.metadata.page_url,
                        "position": chunk.position,
                        "token_count": chunk.token_count,
                        "content": chunk.content,  # Store content for retrieval
                    },
                )
            )

        # Upsert in batches
        for i in range(0, len(indexed_chunks), self.UPSERT_BATCH_SIZE):
            batch = indexed_chunks[i : i + self.UPSERT_BATCH_SIZE]
            try:
                await self._upsert_batch(batch)
                indexed_count += len(batch)
                logger.debug(f"Indexed batch {i // self.UPSERT_BATCH_SIZE + 1}")
            except Exception as e:
                failed_count += len(batch)
                error_msg = f"Failed to upsert batch {i // self.UPSERT_BATCH_SIZE + 1}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Indexing complete: {indexed_count} indexed, {failed_count} failed"
        )

        return IndexingResult(
            total_chunks=len(chunks),
            indexed_chunks=indexed_count,
            failed_chunks=failed_count,
            chapters_processed=sorted(chapters),
            errors=errors,
        )

    async def _upsert_batch(self, chunks: list[IndexedChunk]) -> None:
        """Upsert a batch of indexed chunks to Qdrant.

        Args:
            chunks: List of indexed chunks with embeddings.
        """
        points = [
            {
                "id": chunk.id,
                "vector": chunk.embedding,
                "payload": chunk.metadata,
            }
            for chunk in chunks
        ]

        await self.qdrant_db.upsert_vectors(points)

    async def index_directory(
        self,
        docs_path: Path,
        base_url: str = "",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> IndexingResult:
        """Index all content from a docs directory.

        Args:
            docs_path: Path to the docs directory.
            base_url: Base URL for generating page URLs.
            chunk_size: Target chunk size in tokens.
            chunk_overlap: Token overlap between chunks.

        Returns:
            IndexingResult with statistics about the operation.
        """
        logger.info(f"Parsing content from {docs_path}")

        # Parse and chunk all content
        chunks = parse_textbook_directory(
            docs_path=docs_path,
            base_url=base_url,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        logger.info(f"Parsed {len(chunks)} chunks from directory")

        # Index the chunks
        return await self.index_chunks(chunks)

    async def reindex_chapter(
        self,
        chapter_id: str,
        chunks: list[ContentChunk],
    ) -> IndexingResult:
        """Re-index a specific chapter by deleting old chunks and adding new ones.

        Args:
            chapter_id: ID of the chapter to re-index.
            chunks: New chunks for the chapter.

        Returns:
            IndexingResult with statistics about the operation.
        """
        logger.info(f"Re-indexing chapter: {chapter_id}")

        # Delete existing chunks for this chapter
        await self.delete_chapter(chapter_id)

        # Index new chunks
        return await self.index_chunks(chunks)

    async def delete_chapter(self, chapter_id: str) -> int:
        """Delete all chunks for a specific chapter.

        Args:
            chapter_id: ID of the chapter to delete.

        Returns:
            Number of points deleted (approximate).
        """
        settings = get_settings()

        if not self.qdrant_db.is_connected:
            raise RuntimeError("Qdrant not connected")

        # Use filter to delete by chapter_id
        await self.qdrant_db.client.delete(
            collection_name=settings.qdrant_collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="chapter_id",
                            match=models.MatchValue(value=chapter_id),
                        )
                    ]
                )
            ),
        )

        logger.info(f"Deleted chunks for chapter: {chapter_id}")
        return 0  # Qdrant doesn't return count for filter deletes

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the indexed collection.

        Returns:
            Dictionary with collection statistics.
        """
        health = await self.qdrant_db.health_check()
        return {
            "status": health.get("status"),
            "vectors_count": health.get("vectors_count", 0),
            "collection_exists": health.get("collection_exists", False),
        }


# Global indexer instance
_indexer: QdrantIndexer | None = None


def get_indexer() -> QdrantIndexer:
    """Get the global indexer instance."""
    global _indexer
    if _indexer is None:
        _indexer = QdrantIndexer()
    return _indexer


async def index_textbook_content(
    docs_path: str | Path,
    base_url: str = "",
) -> IndexingResult:
    """Convenience function to index textbook content.

    Args:
        docs_path: Path to the docs directory.
        base_url: Base URL for generating page URLs.

    Returns:
        IndexingResult with statistics about the operation.
    """
    indexer = get_indexer()
    return await indexer.index_directory(
        docs_path=Path(docs_path),
        base_url=base_url,
    )
