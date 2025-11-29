"""Tests for translation service.

Tests the translation engine, RTL formatting, and caching functionality.
Requirements: 8.1, 8.2, 8.3, 8.4
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.translation_service import (
    TranslationService,
    TranslationEngine,
    TranslationCache,
    RTLFormatter,
    TechnicalTermHandler,
    TranslationRequest,
    TranslationResponse,
)


class TestTechnicalTermHandler:
    """Tests for TechnicalTermHandler class."""

    def test_get_transliteration_known_term(self):
        """Test getting transliteration for a known technical term."""
        handler = TechnicalTermHandler()
        result = handler.get_transliteration("robot")
        assert result == "روبوٹ"

    def test_get_transliteration_case_insensitive(self):
        """Test that transliteration lookup is case-insensitive."""
        handler = TechnicalTermHandler()
        assert handler.get_transliteration("ROBOT") == "روبوٹ"
        assert handler.get_transliteration("Robot") == "روبوٹ"

    def test_get_transliteration_unknown_term(self):
        """Test getting transliteration for an unknown term returns None."""
        handler = TechnicalTermHandler()
        result = handler.get_transliteration("unknownterm123")
        assert result is None

    def test_extract_technical_terms(self):
        """Test extracting technical terms from content."""
        handler = TechnicalTermHandler()
        content = "The robot uses AI and machine learning for navigation."
        terms = handler.extract_technical_terms(content)

        # Should find robot, AI, and machine learning
        term_originals = [t.original.lower() for t in terms]
        assert "robot" in term_originals
        assert "ai" in term_originals
        assert "machine learning" in term_originals

    def test_create_term_glossary(self):
        """Test creating a glossary of technical terms."""
        handler = TechnicalTermHandler()
        content = "The robot uses sensors for perception."
        glossary = handler.create_term_glossary(content)

        assert "Technical Terms Glossary:" in glossary
        assert "robot" in glossary.lower()
        assert "sensor" in glossary.lower()

    def test_create_term_glossary_empty_content(self):
        """Test glossary creation with no technical terms."""
        handler = TechnicalTermHandler()
        content = "This is a simple sentence with no technical terms."
        glossary = handler.create_term_glossary(content)
        assert glossary == ""


class TestRTLFormatter:
    """Tests for RTLFormatter class."""

    def test_apply_rtl_formatting(self):
        """Test applying RTL formatting to content."""
        formatter = RTLFormatter()
        content = "اردو متن"
        result = formatter.apply_rtl_formatting(content)

        assert 'dir="rtl"' in result
        assert 'class="rtl-content"' in result
        assert content in result

    def test_has_urdu_content_true(self):
        """Test detecting Urdu content."""
        formatter = RTLFormatter()
        content = "This contains اردو text"
        assert formatter.has_urdu_content(content) is True

    def test_has_urdu_content_false(self):
        """Test detecting non-Urdu content."""
        formatter = RTLFormatter()
        content = "This is English only"
        assert formatter.has_urdu_content(content) is False

    def test_get_rtl_css(self):
        """Test getting RTL CSS styles."""
        formatter = RTLFormatter()
        css = formatter.get_rtl_css()

        assert ".rtl-content" in css
        assert "direction: rtl" in css
        assert "text-align: right" in css

    def test_rtl_css_preserves_code_blocks(self):
        """Test that RTL CSS preserves LTR for code blocks."""
        formatter = RTLFormatter()
        css = formatter.get_rtl_css()

        assert ".rtl-content code" in css
        assert ".rtl-content pre" in css
        assert "direction: ltr" in css


class TestTranslationEngine:
    """Tests for TranslationEngine class."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        # Access class attribute directly without instantiation
        assert TranslationEngine.SYSTEM_PROMPT is not None
        assert "Urdu" in TranslationEngine.SYSTEM_PROMPT
        assert "technical terms" in TranslationEngine.SYSTEM_PROMPT.lower()

    def test_default_model(self):
        """Test default model configuration."""
        assert TranslationEngine.DEFAULT_MODEL == "gpt-4o-mini"

    def test_custom_model(self):
        """Test custom model configuration."""
        with patch("app.services.translation_service.AsyncOpenAI"):
            engine = TranslationEngine(model="gpt-4o")
            assert engine.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_translate_to_urdu_calls_openai(self):
        """Test that translation calls OpenAI API."""
        with patch("app.services.translation_service.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "اردو ترجمہ"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            engine = TranslationEngine()
            result = await engine.translate_to_urdu("Hello world")

            mock_client.chat.completions.create.assert_called_once()
            assert result == "اردو ترجمہ"


class TestTranslationCache:
    """Tests for TranslationCache class."""

    def test_cache_instantiation(self):
        """Test that cache can be instantiated."""
        cache = TranslationCache()
        assert cache is not None

    @pytest.mark.asyncio
    async def test_get_cached_translation_returns_none_when_no_pool(self):
        """Test cache retrieval returns None when database pool is unavailable."""
        with patch("app.services.translation_service.get_postgres_db") as mock_db:
            mock_db.return_value.pool = None

            cache = TranslationCache()
            result = await cache.get_cached_translation("chapter-1", "ur")

            assert result is None

    @pytest.mark.asyncio
    async def test_store_cached_translation_returns_false_when_no_pool(self):
        """Test cache storage returns False when database pool is unavailable."""
        with patch("app.services.translation_service.get_postgres_db") as mock_db:
            mock_db.return_value.pool = None

            cache = TranslationCache()
            result = await cache.store_cached_translation(
                "chapter-1", "translated content", "ur"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_chapter_cache_returns_zero_when_no_pool(self):
        """Test cache invalidation returns 0 when database pool is unavailable."""
        with patch("app.services.translation_service.get_postgres_db") as mock_db:
            mock_db.return_value.pool = None

            cache = TranslationCache()
            result = await cache.invalidate_chapter_cache("chapter-1")

            assert result == 0


class TestTranslationService:
    """Tests for TranslationService class."""

    def test_service_initialization(self):
        """Test service initialization with default components."""
        with patch("app.services.translation_service.AsyncOpenAI"):
            service = TranslationService()

            assert service.translation_engine is not None
            assert service.rtl_formatter is not None
            assert service.cache is not None

    def test_service_with_custom_components(self):
        """Test service initialization with custom components."""
        with patch("app.services.translation_service.AsyncOpenAI"):
            custom_engine = TranslationEngine(model="gpt-4o")
            custom_formatter = RTLFormatter()
            custom_cache = TranslationCache()

            service = TranslationService(
                translation_engine=custom_engine,
                rtl_formatter=custom_formatter,
                cache=custom_cache,
            )

            assert service.translation_engine is custom_engine
            assert service.rtl_formatter is custom_formatter
            assert service.cache is custom_cache

    def test_get_rtl_css(self):
        """Test getting RTL CSS from service."""
        with patch("app.services.translation_service.AsyncOpenAI"):
            service = TranslationService()
            css = service.get_rtl_css()

            assert ".rtl-content" in css
            assert "direction: rtl" in css


class TestTranslationModels:
    """Tests for translation request/response models."""

    def test_translation_request(self):
        """Test TranslationRequest model."""
        request = TranslationRequest(
            chapter_id="chapter-1",
            content="Hello world",
            language="ur",
        )

        assert request.chapter_id == "chapter-1"
        assert request.content == "Hello world"
        assert request.language == "ur"

    def test_translation_request_default_language(self):
        """Test TranslationRequest default language is Urdu."""
        request = TranslationRequest(
            chapter_id="chapter-1",
            content="Hello world",
        )

        assert request.language == "ur"

    def test_translation_response(self):
        """Test TranslationResponse model."""
        response = TranslationResponse(
            chapter_id="chapter-1",
            translated_content="اردو متن",
            language="ur",
            from_cache=False,
            has_rtl_formatting=True,
        )

        assert response.chapter_id == "chapter-1"
        assert response.translated_content == "اردو متن"
        assert response.language == "ur"
        assert response.from_cache is False
        assert response.has_rtl_formatting is True


class TestTranslationEndpoints:
    """Tests for translation API endpoints."""

    def test_translate_endpoint_requires_auth(self):
        """Test that translate endpoint requires authentication."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/translate",
            json={"chapter_id": "chapter-1", "content": "Hello"},
        )

        assert response.status_code == 401

    def test_translate_endpoint_invalid_token(self):
        """Test translate endpoint with invalid token."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/translate",
            json={"chapter_id": "chapter-1", "content": "Hello"},
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

    def test_rtl_css_endpoint(self):
        """Test RTL CSS endpoint returns CSS."""
        from fastapi.testclient import TestClient
        from app.main import app
        import app.services.translation_service as ts

        # Reset global service and mock OpenAI
        ts._translation_service = None
        with patch("app.services.translation_service.AsyncOpenAI"):
            client = TestClient(app)
            response = client.get("/api/translate/css")

            assert response.status_code == 200
            data = response.json()
            assert "css" in data
            assert ".rtl-content" in data["css"]

        # Clean up
        ts._translation_service = None

    def test_cache_invalidation_requires_auth(self):
        """Test that cache invalidation requires authentication."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.delete("/api/translate/cache/chapter-1")

        assert response.status_code == 401
