"""Embedding generation service using OpenAI API.

This module provides functionality to:
- Generate embeddings using OpenAI's text-embedding models
- Handle batch embedding generation for efficiency
- Implement rate limiting and retries

Requirements: 4.1, 4.4
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Sequence

from openai import AsyncOpenAI, RateLimitError, APIError

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    text: str
    embedding: list[float]
    token_count: int


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API."""

    # OpenAI embedding model configuration
    DEFAULT_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536  # Default dimensions for text-embedding-3-small

    # Batch processing configuration
    MAX_BATCH_SIZE = 100  # OpenAI allows up to 2048 inputs per request
    MAX_TOKENS_PER_BATCH = 8000  # Conservative limit for batch token count

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 60.0  # seconds

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize embedding service.

        Args:
            api_key: API key. If not provided, uses config settings.
            model: Embedding model to use. Defaults based on provider.
            base_url: Base URL for API (used for Gemini compatibility).
        """
        settings = get_settings()

        # Use provided values or fall back to config
        self.model = model or settings.active_embedding_model
        effective_api_key = api_key or settings.active_api_key
        effective_base_url = base_url or settings.active_base_url

        # Create client with optional base_url for Gemini compatibility
        if effective_base_url:
            self._client = AsyncOpenAI(
                api_key=effective_api_key,
                base_url=effective_base_url,
            )
        elif effective_api_key:
            self._client = AsyncOpenAI(api_key=effective_api_key)
        else:
            self._client = AsyncOpenAI()

    async def generate_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            EmbeddingResult with embedding vector and token count.
        """
        results = await self.generate_embeddings([text])
        return results[0]

    async def generate_embeddings(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts with batching.

        Args:
            texts: List of texts to embed.

        Returns:
            List of EmbeddingResult objects in the same order as input.
        """
        if not texts:
            return []

        # Process in batches
        all_results: list[EmbeddingResult] = []
        batches = self._create_batches(list(texts))

        for batch_idx, batch in enumerate(batches):
            logger.debug(f"Processing batch {batch_idx + 1}/{len(batches)} with {len(batch)} texts")
            batch_results = await self._process_batch_with_retry(batch)
            all_results.extend(batch_results)

        return all_results

    def _create_batches(self, texts: list[str]) -> list[list[str]]:
        """Split texts into batches respecting size limits.

        Args:
            texts: List of texts to batch.

        Returns:
            List of batches, each containing a subset of texts.
        """
        batches = []
        current_batch = []
        current_tokens = 0

        for text in texts:
            # Estimate tokens (rough approximation: ~4 chars per token)
            estimated_tokens = len(text) // 4

            # Check if adding this text would exceed limits
            if (
                len(current_batch) >= self.MAX_BATCH_SIZE
                or current_tokens + estimated_tokens > self.MAX_TOKENS_PER_BATCH
            ):
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(text)
            current_tokens += estimated_tokens

        # Don't forget the last batch
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _process_batch_with_retry(
        self,
        texts: list[str],
    ) -> list[EmbeddingResult]:
        """Process a batch of texts with retry logic.

        Args:
            texts: Batch of texts to embed.

        Returns:
            List of EmbeddingResult objects.
        """
        retry_delay = self.INITIAL_RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                return await self._process_batch(texts)
            except RateLimitError as e:
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Rate limit exceeded after {self.MAX_RETRIES} retries")
                    raise

                # Extract retry-after if available
                retry_after = getattr(e, "retry_after", None)
                wait_time = retry_after if retry_after else retry_delay

                logger.warning(
                    f"Rate limit hit, waiting {wait_time}s before retry "
                    f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                await asyncio.sleep(wait_time)

                # Exponential backoff
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)

            except APIError as e:
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"API error after {self.MAX_RETRIES} retries: {e}")
                    raise

                logger.warning(
                    f"API error, retrying in {retry_delay}s "
                    f"(attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)

        # Should not reach here, but just in case
        raise RuntimeError("Unexpected state in retry loop")

    async def _process_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Process a single batch of texts.

        Args:
            texts: Batch of texts to embed.

        Returns:
            List of EmbeddingResult objects.
        """
        response = await self._client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # Map results back to input order
        results = []
        for i, text in enumerate(texts):
            embedding_data = response.data[i]
            results.append(
                EmbeddingResult(
                    text=text,
                    embedding=embedding_data.embedding,
                    token_count=response.usage.prompt_tokens // len(texts),  # Approximate per-text
                )
            )

        logger.debug(
            f"Generated {len(results)} embeddings, "
            f"total tokens: {response.usage.total_tokens}"
        )

        return results

    async def close(self) -> None:
        """Close the OpenAI client."""
        await self._client.close()


# Global embedding service instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        settings = get_settings()
        # OpenAI client will use OPENAI_API_KEY env var by default
        _embedding_service = EmbeddingService()
    return _embedding_service


async def close_embedding_service() -> None:
    """Close the global embedding service instance."""
    global _embedding_service
    if _embedding_service is not None:
        await _embedding_service.close()
        _embedding_service = None
