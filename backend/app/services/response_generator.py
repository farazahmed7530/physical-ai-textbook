"""Response generator for RAG pipeline using OpenAI.

This module provides functionality to:
- Generate responses using OpenAI Agents SDK
- Create prompt templates with citation instructions
- Handle selected text context injection
- Implement fallback for no relevant results

Requirements: 3.1, 3.2, 3.3, 3.5
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.context_builder import BuiltContext, ContextBuilder, get_context_builder
from app.services.retriever_service import RetrievedChunk, RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """A source citation for a response."""

    chapter_id: str
    title: str
    section_title: str
    page_url: str
    relevance_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chapter_id": self.chapter_id,
            "title": self.title,
            "section_title": self.section_title,
            "page_url": self.page_url,
            "relevance_score": self.relevance_score,
        }


@dataclass
class GeneratedResponse:
    """Result of response generation."""

    response: str
    sources: list[Source]
    is_fallback: bool = False
    query: str = ""
    selected_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "response": self.response,
            "sources": [s.to_dict() for s in self.sources],
            "is_fallback": self.is_fallback,
            "query": self.query,
            "selected_text": self.selected_text,
        }


# Minimum relevance score threshold for considering results relevant
MIN_RELEVANCE_THRESHOLD = 0.7

# System prompt for the RAG chatbot
SYSTEM_PROMPT = """You are a helpful AI tutor for a Physical AI & Humanoid Robotics textbook. Your role is to answer questions about the textbook content accurately and helpfully.

Guidelines:
1. Base your answers on the provided context from the textbook.
2. Always cite your sources by referencing the source numbers (e.g., [Source 1], [Source 2]).
3. If the user has selected specific text, prioritize explaining that content.
4. Be educational and explain concepts clearly.
5. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can.
6. Use technical terms appropriately but explain them when first introduced.
7. Be concise but thorough in your explanations.

Remember: You are helping students learn about Physical AI and Humanoid Robotics. Be encouraging and supportive."""

FALLBACK_PROMPT = """You are a helpful AI tutor for a Physical AI & Humanoid Robotics textbook. The user has asked a question, but no relevant content was found in the textbook.

Guidelines:
1. Politely acknowledge that you couldn't find specific information in the textbook.
2. Suggest related topics from the textbook that might be helpful.
3. Offer to help with a rephrased question.
4. Be encouraging and supportive.

Available textbook topics include:
- Introduction to Physical AI
- Fundamentals of Humanoid Robotics
- Sensors and Perception
- Motion Planning and Control
- Computer Vision for Robotics
- Natural Language Interaction
- Reinforcement Learning for Robotics
- Human-Robot Interaction
- Safety and Ethics in Physical AI
- Building Your First Robot Project
- Industry Applications
- Future of Physical AI"""


class ResponseGenerator:
    """Service for generating RAG responses using OpenAI."""

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS = 1024
    DEFAULT_TEMPERATURE = 0.7

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        context_builder: ContextBuilder | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """Initialize response generator.

        Args:
            api_key: API key. Uses config settings if not provided.
            model: Model to use for generation.
            base_url: Base URL for API (used for Gemini compatibility).
            context_builder: Context builder instance.
            max_tokens: Maximum tokens for response.
            temperature: Temperature for generation.
        """
        settings = get_settings()

        # Use provided values or fall back to config
        self.model = model or settings.active_chat_model
        self.max_tokens = max_tokens
        self.temperature = temperature

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

        self._context_builder = context_builder

    @property
    def context_builder(self) -> ContextBuilder:
        """Get context builder instance."""
        if self._context_builder is None:
            self._context_builder = get_context_builder()
        return self._context_builder

    def _extract_sources(self, chunks: list[RetrievedChunk]) -> list[Source]:
        """Extract unique sources from chunks.

        Args:
            chunks: List of retrieved chunks.

        Returns:
            List of unique Source objects.
        """
        seen_chapters: set[str] = set()
        sources: list[Source] = []

        for chunk in chunks:
            # Create a unique key for deduplication
            key = f"{chunk.chapter_id}:{chunk.section_title}"
            if key not in seen_chapters:
                seen_chapters.add(key)
                sources.append(
                    Source(
                        chapter_id=chunk.chapter_id,
                        title=chunk.title,
                        section_title=chunk.section_title,
                        page_url=chunk.page_url,
                        relevance_score=chunk.score,
                    )
                )

        return sources

    def _has_relevant_results(self, chunks: list[RetrievedChunk]) -> bool:
        """Check if any chunks meet the relevance threshold.

        Args:
            chunks: List of retrieved chunks.

        Returns:
            True if at least one chunk is relevant.
        """
        if not chunks:
            return False
        return any(chunk.score >= MIN_RELEVANCE_THRESHOLD for chunk in chunks)

    async def generate_response(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        selected_text: str | None = None,
    ) -> GeneratedResponse:
        """Generate a response for a user query.

        Args:
            query: User's question.
            retrieval_result: Result from vector retrieval.
            selected_text: Optional user-selected text for context.

        Returns:
            GeneratedResponse with answer and sources.
        """
        chunks = retrieval_result.chunks

        # Check if we have relevant results
        if not self._has_relevant_results(chunks):
            return await self._generate_fallback_response(query, selected_text)

        # Build context from chunks
        built_context = self.context_builder.build_context(
            chunks=chunks,
            selected_text=selected_text,
        )

        # Generate response with context
        response_text = await self._call_openai(
            query=query,
            context=built_context.context_text,
            is_fallback=False,
        )

        # Extract sources from used chunks
        sources = self._extract_sources(built_context.chunks_used)

        return GeneratedResponse(
            response=response_text,
            sources=sources,
            is_fallback=False,
            query=query,
            selected_text=selected_text,
        )

    async def _generate_fallback_response(
        self,
        query: str,
        selected_text: str | None = None,
    ) -> GeneratedResponse:
        """Generate a fallback response when no relevant content is found.

        Args:
            query: User's question.
            selected_text: Optional user-selected text.

        Returns:
            GeneratedResponse with fallback message.
        """
        logger.info(f"Generating fallback response for query: {query[:100]}...")

        response_text = await self._call_openai(
            query=query,
            context=selected_text or "",
            is_fallback=True,
        )

        return GeneratedResponse(
            response=response_text,
            sources=[],
            is_fallback=True,
            query=query,
            selected_text=selected_text,
        )

    async def _call_openai(
        self,
        query: str,
        context: str,
        is_fallback: bool,
    ) -> str:
        """Call OpenAI API to generate response.

        Args:
            query: User's question.
            context: Context from retrieved chunks.
            is_fallback: Whether this is a fallback response.

        Returns:
            Generated response text.
        """
        system_prompt = FALLBACK_PROMPT if is_fallback else SYSTEM_PROMPT

        # Build user message
        if is_fallback:
            user_message = f"User question: {query}"
            if context:
                user_message = f"User selected text: {context}\n\n{user_message}"
        else:
            user_message = f"{context}\n\nUser question: {query}"

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def close(self) -> None:
        """Close the OpenAI client."""
        await self._client.close()


# Global response generator instance
_response_generator: ResponseGenerator | None = None


def get_response_generator() -> ResponseGenerator:
    """Get the global response generator instance."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator


async def close_response_generator() -> None:
    """Close the global response generator instance."""
    global _response_generator
    if _response_generator is not None:
        await _response_generator.close()
        _response_generator = None
