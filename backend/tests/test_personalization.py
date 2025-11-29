"""Tests for personalization service.

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.main import app
from app.services.personalization_service import (
    ProfileAnalyzer,
    ContentAdapter,
    PersonalizationCache,
    PersonalizationService,
    ExperienceLevel,
    UserProfile,
    ProfileAnalysisResult,
    PersonalizedContentRequest,
    PersonalizedContentResponse,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def profile_analyzer():
    """Create ProfileAnalyzer instance."""
    return ProfileAnalyzer()


class TestProfileAnalyzer:
    """Test ProfileAnalyzer functionality.

    Requirements: 7.1
    """

    def test_analyze_beginner_profile(self, profile_analyzer):
        """Test analysis of beginner profile."""
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="beginner",
            hardware_experience="beginner",
            programming_languages=[],
            robotics_experience=False,
            ai_experience=False,
        )

        result = profile_analyzer.analyze_profile(profile)

        assert result.experience_level == ExperienceLevel.BEGINNER
        assert result.has_complete_profile is True
        assert result.software_score == 0
        assert result.hardware_score == 0
        assert result.domain_score == 0

    def test_analyze_intermediate_profile(self, profile_analyzer):
        """Test analysis of intermediate profile."""
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="intermediate",
            hardware_experience="intermediate",
            programming_languages=["Python", "JavaScript"],
            robotics_experience=False,
            ai_experience=True,
        )

        result = profile_analyzer.analyze_profile(profile)

        assert result.experience_level == ExperienceLevel.INTERMEDIATE
        assert result.has_complete_profile is True
        assert result.software_score == 1
        assert result.hardware_score == 1
        assert result.domain_score == 1  # AI experience only

    def test_analyze_advanced_profile(self, profile_analyzer):
        """Test analysis of advanced profile."""
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="advanced",
            hardware_experience="advanced",
            programming_languages=["Python", "C++", "Rust", "JavaScript", "Go"],
            robotics_experience=True,
            ai_experience=True,
        )

        result = profile_analyzer.analyze_profile(profile)

        assert result.experience_level == ExperienceLevel.ADVANCED
        assert result.has_complete_profile is True
        assert result.software_score == 2
        assert result.hardware_score == 2
        assert result.domain_score == 2  # Both robotics and AI

    def test_incomplete_profile_detection(self, profile_analyzer):
        """Test detection of incomplete profile.

        Requirements: 7.3
        """
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience=None,
            hardware_experience=None,
            programming_languages=None,
            robotics_experience=False,
            ai_experience=False,
        )

        result = profile_analyzer.analyze_profile(profile)

        assert result.has_complete_profile is False
        assert result.experience_level == ExperienceLevel.BEGINNER  # Default

    def test_partial_profile_is_complete(self, profile_analyzer):
        """Test that partial profile with some data is considered complete."""
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="intermediate",
            hardware_experience=None,
            programming_languages=None,
            robotics_experience=False,
            ai_experience=False,
        )

        result = profile_analyzer.analyze_profile(profile)

        assert result.has_complete_profile is True

    def test_programming_languages_bonus(self, profile_analyzer):
        """Test that programming languages add bonus to score."""
        # Profile with many languages
        profile_many_langs = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="intermediate",
            hardware_experience="intermediate",
            programming_languages=["Python", "JavaScript", "C++", "Rust", "Go"],
            robotics_experience=False,
            ai_experience=False,
        )

        # Profile with few languages
        profile_few_langs = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="intermediate",
            hardware_experience="intermediate",
            programming_languages=["Python"],
            robotics_experience=False,
            ai_experience=False,
        )

        result_many = profile_analyzer.analyze_profile(profile_many_langs)
        result_few = profile_analyzer.analyze_profile(profile_few_langs)

        # Many languages should result in higher level
        assert result_many.experience_level.value >= result_few.experience_level.value

    def test_reasoning_generation(self, profile_analyzer):
        """Test that reasoning is generated correctly."""
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            software_experience="advanced",
            hardware_experience="intermediate",
            programming_languages=["Python", "JavaScript"],
            robotics_experience=True,
            ai_experience=False,
        )

        result = profile_analyzer.analyze_profile(profile)

        assert "software experience: advanced" in result.reasoning
        assert "hardware experience: intermediate" in result.reasoning
        assert "2 programming language" in result.reasoning
        assert "robotics experience" in result.reasoning


class TestExperienceLevel:
    """Test ExperienceLevel enum."""

    def test_experience_level_values(self):
        """Test experience level enum values."""
        assert ExperienceLevel.BEGINNER.value == "beginner"
        assert ExperienceLevel.INTERMEDIATE.value == "intermediate"
        assert ExperienceLevel.ADVANCED.value == "advanced"


class TestContentAdapter:
    """Test ContentAdapter functionality.

    Requirements: 7.1, 7.2
    """

    def test_adaptation_prompts_exist(self):
        """Test that adaptation prompts exist for all levels."""
        # Access class attribute directly without instantiating
        assert ExperienceLevel.BEGINNER in ContentAdapter.ADAPTATION_PROMPTS
        assert ExperienceLevel.INTERMEDIATE in ContentAdapter.ADAPTATION_PROMPTS
        assert ExperienceLevel.ADVANCED in ContentAdapter.ADAPTATION_PROMPTS

    def test_beginner_prompt_mentions_simple_language(self):
        """Test beginner prompt emphasizes simple language."""
        prompt = ContentAdapter.ADAPTATION_PROMPTS[ExperienceLevel.BEGINNER]

        assert "simple" in prompt.lower() or "clear" in prompt.lower()
        assert "PRESERVE" in prompt  # Technical terms preserved

    def test_advanced_prompt_mentions_technical_depth(self):
        """Test advanced prompt emphasizes technical depth."""
        prompt = ContentAdapter.ADAPTATION_PROMPTS[ExperienceLevel.ADVANCED]

        assert "technical" in prompt.lower()
        assert "PRESERVE" in prompt  # Technical terms preserved

    @pytest.mark.asyncio
    async def test_adapt_content_calls_openai(self):
        """Test that adapt_content calls OpenAI API."""
        with patch('app.services.personalization_service.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Adapted content"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            adapter = ContentAdapter(api_key="test-key")
            adapter._client = mock_client

            result = await adapter.adapt_content(
                "Original content about robotics",
                ExperienceLevel.BEGINNER,
            )

            assert result == "Adapted content"
            mock_client.chat.completions.create.assert_called_once()


class TestPersonalizationCache:
    """Test PersonalizationCache functionality.

    Requirements: 7.4
    """

    @pytest.mark.asyncio
    async def test_get_cached_content_returns_none_when_no_pool(self):
        """Test cache returns None when database pool is not available."""
        with patch('app.services.personalization_service.get_postgres_db') as mock_db:
            mock_db.return_value.pool = None

            cache = PersonalizationCache()
            result = await cache.get_cached_content("user-id", "chapter-id")

            assert result is None

    @pytest.mark.asyncio
    async def test_store_cached_content_returns_false_when_no_pool(self):
        """Test cache storage returns False when database pool is not available."""
        with patch('app.services.personalization_service.get_postgres_db') as mock_db:
            mock_db.return_value.pool = None

            cache = PersonalizationCache()
            result = await cache.store_cached_content(
                "user-id", "chapter-id", "content", "beginner"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_user_cache_returns_zero_when_no_pool(self):
        """Test cache invalidation returns 0 when database pool is not available."""
        with patch('app.services.personalization_service.get_postgres_db') as mock_db:
            mock_db.return_value.pool = None

            cache = PersonalizationCache()
            result = await cache.invalidate_user_cache("user-id")

            assert result == 0


class TestPersonalizationService:
    """Test PersonalizationService functionality.

    Requirements: 7.1, 7.2, 7.3, 7.4
    """

    def test_service_initialization_with_mocked_adapter(self):
        """Test service initializes with mocked content adapter."""
        with patch('app.services.personalization_service.AsyncOpenAI'):
            mock_adapter = MagicMock(spec=ContentAdapter)
            service = PersonalizationService(content_adapter=mock_adapter)

            assert service.profile_analyzer is not None
            assert service.content_adapter is mock_adapter
            assert service.cache is not None

    def test_service_with_custom_components(self):
        """Test service accepts custom components."""
        custom_analyzer = ProfileAnalyzer()
        custom_cache = PersonalizationCache()
        mock_adapter = MagicMock(spec=ContentAdapter)

        service = PersonalizationService(
            profile_analyzer=custom_analyzer,
            content_adapter=mock_adapter,
            cache=custom_cache,
        )

        assert service.profile_analyzer is custom_analyzer
        assert service.cache is custom_cache
        assert service.content_adapter is mock_adapter


class TestPersonalizationEndpoints:
    """Test personalization API endpoints."""

    def test_personalize_endpoint_requires_auth(self, client):
        """Test personalization endpoint requires authentication."""
        response = client.post(
            "/api/personalize",
            json={
                "chapter_id": "intro",
                "content": "Some content",
            },
        )

        assert response.status_code == 401

    def test_personalize_endpoint_invalid_token(self, client):
        """Test personalization endpoint with invalid token returns 401."""
        response = client.post(
            "/api/personalize",
            json={
                "chapter_id": "intro",
                "content": "Some content",
            },
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

    def test_personalize_endpoint_missing_fields(self, client):
        """Test personalization endpoint with missing fields returns 422."""
        response = client.post(
            "/api/personalize",
            json={},
            headers={"Authorization": "Bearer some_token"},
        )

        # Will be 401 first due to invalid token, but if auth passed, would be 422
        assert response.status_code in [401, 422]

    def test_cache_invalidation_requires_auth(self, client):
        """Test cache invalidation endpoint requires authentication."""
        response = client.delete("/api/personalize/cache")

        assert response.status_code == 401


class TestUserProfile:
    """Test UserProfile dataclass."""

    def test_user_profile_creation(self):
        """Test UserProfile can be created with all fields."""
        user_id = str(uuid.uuid4())
        profile = UserProfile(
            user_id=user_id,
            software_experience="intermediate",
            hardware_experience="beginner",
            programming_languages=["Python", "JavaScript"],
            robotics_experience=True,
            ai_experience=False,
        )

        assert profile.user_id == user_id
        assert profile.software_experience == "intermediate"
        assert profile.hardware_experience == "beginner"
        assert profile.programming_languages == ["Python", "JavaScript"]
        assert profile.robotics_experience is True
        assert profile.ai_experience is False

    def test_user_profile_defaults(self):
        """Test UserProfile has correct defaults."""
        profile = UserProfile(user_id=str(uuid.uuid4()))

        assert profile.software_experience is None
        assert profile.hardware_experience is None
        assert profile.programming_languages is None
        assert profile.robotics_experience is False
        assert profile.ai_experience is False


class TestPersonalizedContentModels:
    """Test Pydantic models for personalization."""

    def test_personalized_content_request(self):
        """Test PersonalizedContentRequest model."""
        request = PersonalizedContentRequest(
            chapter_id="intro",
            user_id=str(uuid.uuid4()),
            original_content="Some content about robotics",
        )

        assert request.chapter_id == "intro"
        assert request.original_content == "Some content about robotics"

    def test_personalized_content_response(self):
        """Test PersonalizedContentResponse model."""
        response = PersonalizedContentResponse(
            chapter_id="intro",
            user_id=str(uuid.uuid4()),
            personalized_content="Adapted content",
            experience_level="beginner",
            from_cache=False,
        )

        assert response.chapter_id == "intro"
        assert response.personalized_content == "Adapted content"
        assert response.experience_level == "beginner"
        assert response.from_cache is False
