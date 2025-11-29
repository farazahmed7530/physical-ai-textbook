"""Context builder for RAG response generation.

This module provides functionality to:
- Assemble retrieved chunks into coherent context
- Handle context window limits
- Prioritize most relevant chunks

Requirements: 3.1
"""

import logging
from dataclasses import dataclass

from app.services.retriever_service import RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class BuiltContext:
    """Result of context building."""

    context_text: str
    chunks_used: list[RetrievedChunk]
    total_tokens_estimate: int
    truncated: bool


class ContextBuilder:
    """Service for assembling retrieved chunks into coherent context."""

    # Default context limits
    DEFAULT_MAX_TOKENS = 4000  # Conservative limit for context window
    DEFAULT_MAX_CHUNKS = 10
    CHARS_PER_TOKEN_ESTIMATE = 4  # Rough estimate for token counting

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_chunks: int = DEFAULT_MAX_CHUNKS,
    ):
        """Initialize context builder.

        Args:
            max_tokens: Maximum estimated tokens for context.
            max_chunks: Maximum number of chunks to include.
        """
        self.max_tokens = max_tokens
        self.max_chunks = max_chunks

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate tokens for.

        Returns:
            Estimated token count.
        """
        return len(text) // self.CHARS_PER_TOKEN_ESTIMATE

    def _format_chunk(self, chunk: RetrievedChunk, index: int) -> str:
        """Format a single chunk for context.

        Args:
            chunk: The retrieved chunk.
            index: Index of the chunk (1-based for display).

        Returns:
            Formatted chunk string.
        """
        return (
            f"[Source {index}: {chunk.title} - {chunk.section_title}]\n"
            f"{chunk.content}\n"
        )

    def build_context(
        self,
        chunks: list[RetrievedChunk],
        selected_text: str | None = None,
    ) -> BuiltContext:
        """Build context from retrieved chunks.

        Chunks are assumed to be pre-sorted by relevance score (highest first).
        The builder prioritizes higher-scoring chunks and respects token limits.

        Args:
            chunks: List of retrieved chunks, sorted by relevance.
            selected_text: Optional user-selected text for additional context.

        Returns:
            BuiltContext with assembled context and metadata.
        """
        if not chunks:
            return BuiltContext(
                context_text="",
                chunks_used=[],
                total_tokens_estimate=0,
                truncated=False,
            )

        context_parts: list[str] = []
        chunks_used: list[RetrievedChunk] = []
        current_tokens = 0
        truncated = False

        # Add selected text context first if provided
        if selected_text:
            selected_context = f"[User Selected Text]\n{selected_text}\n\n"
            selected_tokens = self._estimate_tokens(selected_context)
            context_parts.append(selected_context)
            current_tokens += selected_tokens

        # Add header for retrieved content
        header = "Relevant content from the textbook:\n\n"
        header_tokens = self._estimate_tokens(header)
        context_parts.append(header)
        current_tokens += header_tokens

        # Add chunks in order of relevance (already sorted)
        for i, chunk in enumerate(chunks):
            if len(chunks_used) >= self.max_chunks:
                truncated = True
                break

            formatted = self._format_chunk(chunk, len(chunks_used) + 1)
            chunk_tokens = self._estimate_tokens(formatted)

            # Check if adding this chunk would exceed token limit
            if current_tokens + chunk_tokens > self.max_tokens:
                truncated = True
                break

            context_parts.append(formatted)
            chunks_used.append(chunk)
            current_tokens += chunk_tokens

        context_text = "\n".join(context_parts)

        logger.debug(
            f"Built context with {len(chunks_used)} chunks, "
            f"~{current_tokens} tokens, truncated={truncated}"
        )

        return BuiltContext(
            context_text=context_text,
            chunks_used=chunks_used,
            total_tokens_estimate=current_tokens,
            truncated=truncated,
        )

    def build_context_with_priority(
      self,
        chunks: list[RetrievedChunk],
        priority_chapter_id: str | None = None,
        selected_text: str | None = None,
    ) -> BuiltContext:
        """Build context with optional chapter prioritization.

        Args:
            chunks: List of retrieved chunks.
            priority_chapter_id: Chapter ID to prioritize in ordering.
            selected_text: Optional user-selected text for additional context.

        Returns:
            BuiltContext with assembled context and metadata.
        """
        if not priority_chapter_id:
            return self.build_context(chunks, selected_text)

        # Reorder chunks to prioritize the specified chapter
        # while maintaining relative score ordering within groups
        priority_chunks = [c for c in chunks if c.chapter_id == priority_chapter_id]
        other_chunks = [c for c in chunks if c.chapter_id != priority_chapter_id]

        reordered = priority_chunks + other_chunks
        return self.build_context(reordered, selected_text)


# Global context builder instance
_context_builder: ContextBuilder | None = None


def get_context_builder() -> ContextBuilder:
    """Get the global context builder instance."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
