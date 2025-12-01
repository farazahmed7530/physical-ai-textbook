"""Tests for RAG response generation services.

Requirements: 3.1, 3.2, 3.3, 3.5
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.context_builder import ContextBuilder, BuiltContext
from app.services.response_generator import (
    ResponseGenerator,
    GeneratedResponse,
    Source,
    MIN_RELEVANCE_THRESHOLD,
)
from app.services.rag_service import RAGService, RAGRequest, RAGResponse
from app.services.retriever_service import RetrievedChunk, RetrievalResult


def create_mock_chunk(
    id: str = "chunk-1",
    content: str = "Test content about robotics",
    chapter_id: str = "motion-planning",
    title: str = "Motion Planning",
    section_title: str = "Introduction",
    page_url: str = "/core/motion-planning",
    position: int = 0,
    score: float = 0.9,
) -> RetrievedChunk:
    """Create a mock RetrievedChunk for testing."""
    return RetrievedChunk(
        id=id,
        content=content,
        chapter_id=chapter_id,
        title=title,
        section_title=section_title,
        page_url=page_url,
        position=position,
        score=score,
    )


class TestContextBuilder:
    """Tests for ContextBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create context builder instance."""
        return ContextBuilder(max_tokens=1000, max_chunks=5)

    def test_build_context_empty_chunks(self, builder):
        """Test building context with no chunks."""
        result = builder.build_context([])

        assert result.context_text == ""
        assert result.chunks_used == []
        assert result.total_tokens_estimate == 0
        assert result.truncated is False

    def test_build_context_single_chunk(self, builder):
        """Test building context with a single chunk."""
        chunk = create_mock_chunk()
        result = builder.build_context([chunk])

        assert len(result.chunks_used) == 1
        assert chunk in result.chunks_used
        assert "Motion Planning" in result.context_text
        assert "Introduction" in result.context_text
        assert result.truncated is False

    def test_build_context_multiple_chunks(self, builder):
        """Test building context with multiple chunks."""
        chunks = [
            create_mock_chunk(id="1", score=0.95),
            create_mock_chunk(id="2", score=0.85, section_title="Algorithms"),
            create_mock_chunk(id="3", score=0.75, section_title="Examples"),
        ]
        result = builder.build_context(chunks)

        assert len(result.chunks_used) == 3
        assert "[Source 1:" in result.context_text
        assert "[Source 2:" in result.context_text
        assert "[Source 3:" in result.context_text

    def test_build_context_with_selected_text(self, builder):
        """Test building context with user-selected text."""
        chunk = create_mock_chunk()
        selected_text = "This is the user's selected text"

        result = builder.build_context([chunk], selected_text=selected_text)

        assert "[User Selected Text]" in result.context_text
        assert selected_text in result.context_text

    def test_build_context_respects_max_chunks(self):
        """Test that context builder respects max_chunks limit."""
        builder = ContextBuilder(max_tokens=10000, max_chunks=2)
        chunks = [
            create_mock_chunk(id=str(i), score=0.9 - i * 0.1)
            for i in range(5)
        ]

        result = builder.build_context(chunks)

        assert len(result.chunks_used) == 2
        assert result.truncated is True

    def test_build_context_respects_max_tokens(self):
        """Test that context builder respects max_tokens limit."""
        builder = ContextBuilder(max_tokens=100, max_chunks=10)
        # Create chunks with long content
        chunks = [
            create_mock_chunk(
                id=str(i),
                content="A" * 200,  # Long content
                score=0.9,
            )
            for i in range(5)
        ]

        result = builder.build_context(chunks)

        # Should truncate due to token limit
        assert len(result.chunks_used) < 5
        assert result.truncated is True

    def test_build_context_with_priority(self, builder):
        """Test building context with chapter prioritization."""
        chunks = [
            create_mock_chunk(id="1", chapter_id="vision", score=0.95),
            create_mock_chunk(id="2", chapter_id="motion", score=0.90),
            create_mock_chunk(id="3", chapter_id="motion", score=0.85),
        ]

        result = builder.build_context_with_priority(
            chunks, priority_chapter_id="motion"
        )

        # Motion chapter chunks should come first
        assert result.chunks_used[0].chapter_id == "motion"
        assert result.chunks_used[1].chapter_id == "motion"

    def test_estimate_tokens(self, builder):
        """Test token estimation."""
        text = "This is a test string"
        tokens = builder._estimate_tokens(text)

        # Should be roughly len(text) / 4
        assert tokens == len(text) // 4


class TestResponseGenerator:
    """Tests for ResponseGenerator class."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response about robotics."
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        return mock_client

    @pytest.fixture
    def generator(self, mock_openai_client):
        """Create response generator with mocked client."""
        gen = ResponseGenerator(api_key="test-api-key")
        gen._client = mock_openai_client
        return gen

    def test_extract_sources_deduplicates(self, generator):
        """Test that source extraction deduplicates by chapter+section."""
        chunks = [
            create_mock_chunk(id="1", chapter_id="ch1", section_title="sec1"),
            create_mock_chunk(id="2", chapter_id="ch1", section_title="sec1"),
            create_mock_chunk(id="3", chapter_id="ch1", section_title="sec2"),
        ]

        sources = generator._extract_sources(chunks)

        # Should have 2 unique sources (ch1:sec1 and ch1:sec2)
        assert len(sources) == 2

    def test_has_relevant_results_true(self, generator):
        """Test relevance check with relevant chunks."""
        chunks = [
            create_mock_chunk(score=0.8),
            create_mock_chunk(score=0.6),
        ]

        assert generator._has_relevant_results(chunks) is True

    def test_has_relevant_results_false(self, generator):
        """Test relevance check with no relevant chunks."""
        chunks = [
            create_mock_chunk(score=0.4),  # Below 0.5 threshold
            create_mock_chunk(score=0.3),
        ]

        assert generator._has_relevant_results(chunks) is False

    def test_has_relevant_results_empty(self, generator):
        """Test relevance check with empty chunks."""
        assert generator._has_relevant_results([]) is False

    @pytest.mark.asyncio
    async def test_generate_response_with_relevant_chunks(self, generator):
        """Test response generation with relevant chunks."""
        chunks = [create_mock_chunk(score=0.9)]
        retrieval_result = RetrievalResult(
            query="What is motion planning?",
            processed_query="what is motion planning?",
            chunks=chunks,
            total_found=1,
        )

        result = await generator.generate_response(
            query="What is motion planning?",
            retrieval_result=retrieval_result,
        )

        assert isinstance(result, GeneratedResponse)
        assert result.is_fallback is False
        assert len(result.sources) > 0
        assert result.response != ""

    @pytest.mark.asyncio
    async def test_generate_response_fallback(self, generator):
        """Test fallback response when no relevant chunks."""
        chunks = [create_mock_chunk(score=0.4)]  # Below 0.5 threshold
        retrieval_result = RetrievalResult(
            query="What is quantum computing?",
            processed_query="what is quantum computing?",
            chunks=chunks,
            total_found=1,
        )

        result = await generator.generate_response(
            query="What is quantum computing?",
            retrieval_result=retrieval_result,
        )

        assert result.is_fallback is True
        assert result.sources == []

    @pytest.mark.asyncio
    async def test_generate_response_with_selected_text(self, generator):
        """Test response generation with selected text."""
        chunks = [create_mock_chunk(score=0.9)]
        retrieval_result = RetrievalResult(
            query="Explain this",
            processed_query="explain this",
            chunks=chunks,
            total_found=1,
        )
        selected_text = "Motion planning is the process..."

        result = await generator.generate_response(
            query="Explain this",
            retrieval_result=retrieval_result,
            selected_text=selected_text,
        )

        assert result.selected_text == selected_text

    @pytest.mark.asyncio
    async def test_call_openai_normal(self, generator, mock_openai_client):
        """Test OpenAI API call for normal response."""
        result = await generator._call_openai(
            query="What is robotics?",
            context="Robotics is the study of robots.",
            is_fallback=False,
        )

        assert result == "This is a test response about robotics."
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_openai_fallback(self, generator, mock_openai_client):
        """Test OpenAI API call for fallback response."""
        result = await generator._call_openai(
            query="What is quantum computing?",
            context="",
            is_fallback=True,
        )

        assert result == "This is a test response about robotics."
        mock_openai_client.chat.completions.create.assert_called_once()


class TestSource:
    """Tests for Source dataclass."""

    def test_to_dict(self):
        """Test Source serialization."""
        source = Source(
            chapter_id="motion-planning",
            title="Motion Planning",
            section_title="Introduction",
            page_url="/core/motion-planning",
            relevance_score=0.95,
        )

        result = source.to_dict()

        assert result["chapter_id"] == "motion-planning"
        assert result["title"] == "Motion Planning"
        assert result["section_title"] == "Introduction"
        assert result["page_url"] == "/core/motion-planning"
        assert result["relevance_score"] == 0.95


class TestGeneratedResponse:
    """Tests for GeneratedResponse dataclass."""

    def test_to_dict(self):
        """Test GeneratedResponse serialization."""
        source = Source(
            chapter_id="ch1",
            title="Title",
            section_title="Section",
            page_url="/url",
            relevance_score=0.9,
        )
        response = GeneratedResponse(
            response="Test response",
            sources=[source],
            is_fallback=False,
            query="Test query",
            selected_text="Selected",
        )

        result = response.to_dict()

        assert result["response"] == "Test response"
        assert len(result["sources"]) == 1
        assert result["is_fallback"] is False
        assert result["query"] == "Test query"
        assert result["selected_text"] == "Selected"


class TestRAGService:
    """Tests for RAGService class."""

    @pytest.fixture
    def mock_retriever(self):
        """Create mock retriever."""
        mock = MagicMock()
        mock.retrieve = AsyncMock(
            return_value=RetrievalResult(
                query="test query",
                processed_query="test query",
                chunks=[create_mock_chunk(score=0.9)],
                total_found=1,
            )
        )
        return mock

    @pytest.fixture
    def mock_response_generator(self):
        """Create mock response generator."""
        mock = MagicMock()
        mock.generate_response = AsyncMock(
            return_value=GeneratedResponse(
                response="Test response",
                sources=[
                    Source(
                        chapter_id="ch1",
                        title="Title",
                        section_title="Section",
                        page_url="/url",
                        relevance_score=0.9,
                    )
                ],
                is_fallback=False,
                query="test query",
                selected_text=None,
            )
        )
        return mock

    @pytest.fixture
    def rag_service(self, mock_retriever, mock_response_generator):
        """Create RAG service with mocks."""
        return RAGService(
            retriever=mock_retriever,
            response_generator=mock_response_generator,
        )

    @pytest.mark.asyncio
    async def test_process_query(self, rag_service, mock_retriever, mock_response_generator):
        """Test RAG query processing."""
        request = RAGRequest(
            query="What is motion planning?",
            top_k=5,
            score_threshold=0.7,
        )

        result = await rag_service.process_query(request)

        assert isinstance(result, RAGResponse)
        assert result.response == "Test response"
        assert len(result.sources) == 1
        assert result.is_fallback is False

        mock_retriever.retrieve.assert_called_once_with(
            query="What is motion planning?",
            top_k=5,
            score_threshold=0.7,
        )

    @pytest.mark.asyncio
    async def test_process_query_with_selected_text(
        self, rag_service, mock_retriever, mock_response_generator
    ):
        """Test RAG query with selected text."""
        request = RAGRequest(
            query="Explain this",
            selected_text="Motion planning involves...",
        )

        await rag_service.process_query(request)

        # Verify selected text was passed to response generator
        call_args = mock_response_generator.generate_response.call_args
        assert call_args.kwargs["selected_text"] == "Motion planning involves..."


class TestRAGResponse:
    """Tests for RAGResponse dataclass."""

    def test_to_dict(self):
        """Test RAGResponse serialization."""
        response = RAGResponse(
            response="Test response",
            sources=[{"chapter_id": "ch1", "title": "Title"}],
            is_fallback=False,
            query="Test query",
            selected_text="Selected",
        )

        result = response.to_dict()

        assert result["response"] == "Test response"
        assert len(result["sources"]) == 1
        assert result["is_fallback"] is False
        assert result["query"] == "Test query"
        assert result["selected_text"] == "Selected"
