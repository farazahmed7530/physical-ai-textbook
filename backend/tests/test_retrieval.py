"""Tests for query processor and vector retriever services.

Requirements: 4.2
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.query_processor import (
    QueryProcessor,
    ProcessedQuery,
)
from app.services.retriever_service import (
    VectorRetriever,
    RetrievedChunk,
    RetrievalResult,
)
from app.services.embedding_service import EmbeddingResult


class TestQueryProcessor:
    """Tests for QueryProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create processor instance without embedding service."""
        return QueryProcessor(enable_expansion=True)

    def test_preprocess_query_normalizes_whitespace(self, processor):
        """Test that preprocessing normalizes whitespace."""
        query = "  What   is   robot   motion  planning?  "
        result = processor.preprocess_query(query)
        assert result == "what is robot motion planning?"

    def test_preprocess_query_lowercases(self, processor):
        """Test that preprocessing converts to lowercase."""
        query = "What Is ROBOT Motion Planning?"
        result = processor.preprocess_query(query)
        assert result == "what is robot motion planning?"

    def test_preprocess_query_removes_punctuation(self, processor):
        """Test that preprocessing removes excessive punctuation."""
        query = "What is robot!!! motion... planning???"
        result = processor.preprocess_query(query)
        # Should keep question marks but remove others
        assert "!!!" not in result
        assert "..." not in result

    def test_expand_query_finds_synonyms(self, processor):
        """Test that query expansion finds domain synonyms."""
        query = "robot motion control"
        expanded = processor.expand_query(query)

        # Should find synonyms for robot, motion, control
        assert len(expanded) > 0
        # Check for some expected expansions
        all_expansions = " ".join(expanded).lower()
        assert any(term in all_expansions for term in ["robotics", "movement", "controller"])

    def test_expand_query_no_duplicates(self, processor):
        """Test that expansion doesn't add terms already in query."""
        query = "robotics and humanoid robots"
        expanded = processor.expand_query(query)

        # Should not include "robotics" since it's already in query
        for term in expanded:
            assert term.lower() not in query.lower()

    def test_expand_query_disabled(self):
        """Test that expansion can be disabled."""
        processor = QueryProcessor(enable_expansion=False)
        query = "robot motion control"
        expanded = processor.expand_query(query)
        assert expanded == []

    def test_expand_query_filters_stop_words(self, processor):
        """Test that stop words are filtered before expansion."""
        query = "what is the robot"
        expanded = processor.expand_query(query)

        # Only "robot" should be considered for expansion
        # Stop words like "what", "is", "the" should be ignored
        assert len(expanded) > 0

    def test_build_embedding_text_without_expansions(self, processor):
        """Test building embedding text without expansions."""
        result = processor.build_embedding_text("robot motion", [])
        assert result == "robot motion"

    def test_build_embedding_text_with_expansions(self, processor):
        """Test building embedding text with expansions."""
        result = processor.build_embedding_text(
            "robot motion",
            ["robotics", "movement", "locomotion"]
        )
        assert "robot motion" in result
        assert "robotics" in result
        # Should limit expansions
        assert result.count(" ") < 10  # Not too many terms

    @pytest.mark.asyncio
    async def test_process_query_returns_processed_query(self):
        """Test that process_query returns a ProcessedQuery object."""
        # Mock the embedding service
        mock_embedding_service = MagicMock()
        mock_embedding_service.generate_embedding = AsyncMock(
            return_value=EmbeddingResult(
                text="test query",
                embedding=[0.1] * 1536,
                token_count=2,
            )
        )

        processor = QueryProcessor(
            embedding_service=mock_embedding_service,
            enable_expansion=True,
        )

        result = await processor.process_query("What is robot motion planning?")

        assert isinstance(result, ProcessedQuery)
        assert result.original_query == "What is robot motion planning?"
        assert result.processed_query == "what is robot motion planning?"
        assert len(result.embedding) == 1536
        assert isinstance(result.expanded_terms, list)


class TestVectorRetriever:
    """Tests for VectorRetriever class."""

    @pytest.fixture
    def mock_qdrant_db(self):
        """Create mock Qdrant database."""
        mock_db = MagicMock()
        mock_db.search = AsyncMock(return_value=[
            {
                "id": "chunk-1",
                "score": 0.95,
                "payload": {
                    "content": "Robot motion planning involves...",
                    "chapter_id": "motion-planning",
                    "title": "Motion Planning",
                    "section_title": "Introduction",
                    "page_url": "/core/motion-planning",
                    "position": 0,
                },
            },
            {
                "id": "chunk-2",
                "score": 0.85,
                "payload": {
                    "content": "Path planning algorithms...",
                    "chapter_id": "motion-planning",
                    "title": "Motion Planning",
                    "section_title": "Algorithms",
                    "page_url": "/core/motion-planning",
                    "position": 1,
                },
            },
        ])
        return mock_db

    @pytest.fixture
    def mock_query_processor(self):
        """Create mock query processor."""
        mock_processor = MagicMock()
        mock_processor.process_query = AsyncMock(
            return_value=ProcessedQuery(
                original_query="What is motion planning?",
                processed_query="what is motion planning?",
                expanded_terms=["path planning", "trajectory"],
                embedding=[0.1] * 1536,
            )
        )
        return mock_processor

    @pytest.mark.asyncio
    async def test_retrieve_returns_retrieval_result(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieve returns a RetrievalResult."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
        )

        result = await retriever.retrieve("What is motion planning?")

        assert isinstance(result, RetrievalResult)
        assert result.query == "What is motion planning?"
        assert result.processed_query == "what is motion planning?"
        assert len(result.chunks) == 2
        assert result.total_found == 2

    @pytest.mark.asyncio
    async def test_retrieve_chunks_have_correct_structure(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieved chunks have correct structure."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
        )

        result = await retriever.retrieve("What is motion planning?")

        for chunk in result.chunks:
            assert isinstance(chunk, RetrievedChunk)
            assert chunk.id is not None
            assert chunk.content is not None
            assert chunk.chapter_id is not None
            assert chunk.score > 0

    @pytest.mark.asyncio
    async def test_retrieve_respects_top_k(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieve respects top_k parameter."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
        )

        await retriever.retrieve("test query", top_k=3)

        # Verify search was called with correct limit
        mock_qdrant_db.search.assert_called_once()
        call_kwargs = mock_qdrant_db.search.call_args.kwargs
        assert call_kwargs["limit"] == 3

    @pytest.mark.asyncio
    async def test_retrieve_respects_score_threshold(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieve respects score_threshold parameter."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
        )

        await retriever.retrieve("test query", score_threshold=0.8)

        # Verify search was called with correct threshold
        mock_qdrant_db.search.assert_called_once()
        call_kwargs = mock_qdrant_db.search.call_args.kwargs
        assert call_kwargs["score_threshold"] == 0.8

    @pytest.mark.asyncio
    async def test_retrieve_uses_default_parameters(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieve uses default parameters when not specified."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
            default_top_k=10,
            default_score_threshold=0.75,
        )

        await retriever.retrieve("test query")

        call_kwargs = mock_qdrant_db.search.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["score_threshold"] == 0.75

    @pytest.mark.asyncio
    async def test_retrieve_limits_max_top_k(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieve limits top_k to MAX_TOP_K."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
        )

        await retriever.retrieve("test query", top_k=100)

        call_kwargs = mock_qdrant_db.search.call_args.kwargs
        assert call_kwargs["limit"] <= VectorRetriever.MAX_TOP_K

    @pytest.mark.asyncio
    async def test_retrieve_with_embedding(self, mock_qdrant_db):
        """Test retrieve_with_embedding method."""
        retriever = VectorRetriever(qdrant_db=mock_qdrant_db)

        embedding = [0.1] * 1536
        chunks = await retriever.retrieve_with_embedding(embedding, top_k=5)

        assert len(chunks) == 2
        assert all(isinstance(c, RetrievedChunk) for c in chunks)
        mock_qdrant_db.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_by_chapter_filters_results(
        self, mock_qdrant_db, mock_query_processor
    ):
        """Test that retrieve_by_chapter filters by chapter_id."""
        retriever = VectorRetriever(
            qdrant_db=mock_qdrant_db,
            query_processor=mock_query_processor,
        )

        result = await retriever.retrieve_by_chapter(
            query="test query",
            chapter_id="motion-planning",
        )

        # All chunks should be from the specified chapter
        for chunk in result.chunks:
            assert chunk.chapter_id == "motion-planning"

    @pytest.mark.asyncio
    async def test_retrieve_by_chapter_excludes_other_chapters(
        self, mock_query_processor
    ):
        """Test that retrieve_by_chapter excludes other chapters."""
        # Mock with mixed chapter results
        mock_db = MagicMock()
        mock_db.search = AsyncMock(return_value=[
            {
                "id": "chunk-1",
                "score": 0.95,
                "payload": {
                    "content": "Content 1",
                    "chapter_id": "motion-planning",
                    "title": "Motion Planning",
                    "section_title": "Intro",
                    "page_url": "/motion-planning",
                    "position": 0,
                },
            },
            {
                "id": "chunk-2",
                "score": 0.90,
                "payload": {
                    "content": "Content 2",
                    "chapter_id": "computer-vision",
                    "title": "Computer Vision",
                    "section_title": "Intro",
                    "page_url": "/computer-vision",
                    "position": 0,
                },
            },
        ])

        retriever = VectorRetriever(
            qdrant_db=mock_db,
            query_processor=mock_query_processor,
        )

        result = await retriever.retrieve_by_chapter(
            query="test query",
            chapter_id="motion-planning",
        )

        assert len(result.chunks) == 1
        assert result.chunks[0].chapter_id == "motion-planning"


class TestRetrievedChunk:
    """Tests for RetrievedChunk dataclass."""

    def test_to_dict(self):
        """Test RetrievedChunk serialization."""
        chunk = RetrievedChunk(
            id="test-id",
            content="Test content",
            chapter_id="test-chapter",
            title="Test Title",
            section_title="Test Section",
            page_url="/test",
            position=0,
            score=0.95,
        )

        result = chunk.to_dict()

        assert result["id"] == "test-id"
        assert result["content"] == "Test content"
        assert result["chapter_id"] == "test-chapter"
        assert result["title"] == "Test Title"
        assert result["section_title"] == "Test Section"
        assert result["page_url"] == "/test"
        assert result["position"] == 0
        assert result["score"] == 0.95


class TestRetrievalResult:
    """Tests for RetrievalResult dataclass."""

    def test_to_dict(self):
        """Test RetrievalResult serialization."""
        chunk = RetrievedChunk(
            id="test-id",
            content="Test content",
            chapter_id="test-chapter",
            title="Test Title",
            section_title="Test Section",
            page_url="/test",
            position=0,
            score=0.95,
        )

        result = RetrievalResult(
            query="test query",
            processed_query="test query",
            chunks=[chunk],
            total_found=1,
        )

        result_dict = result.to_dict()

        assert result_dict["query"] == "test query"
        assert result_dict["processed_query"] == "test query"
        assert len(result_dict["chunks"]) == 1
        assert result_dict["total_found"] == 1
