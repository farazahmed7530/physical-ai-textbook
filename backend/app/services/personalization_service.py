"""Personalization service for adapting content based on user background.

This module provides functionality to:
- Analyze user profiles to determine content complexity level
- Adapt content using OpenAI while preserving technical terms
- Cache personalized content in PostgreSQL

Requirements: 7.1, 7.2, 7.4
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings
from app.db.postgres import get_postgres_db

logger = logging.getLogger(__name__)


class ExperienceLevel(str, Enum):
    """User experience level for content personalization."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class UserProfile:
    """User profile data for personalization analysis."""
    user_id: str
    software_experience: Optional[str] = None
    hardware_experience: Optional[str] = None
    programming_languages: Optional[list[str]] = None
    robotics_experience: bool = False
    ai_experience: bool = False


@dataclass
class ProfileAnalysisResult:
    """Result of profile analysis."""
    experience_level: ExperienceLevel
    has_complete_profile: bool
    software_score: int  # 0-2 (beginner=0, intermediate=1, advanced=2)
    hardware_score: int  # 0-2
    domain_score: int    # 0-2 based on robotics/AI experience
    reasoning: str


class PersonalizedContentRequest(BaseModel):
    """Request schema for content personalization."""
    chapter_id: str
    user_id: str
    original_content: str


class PersonalizedContentResponse(BaseModel):
    """Response schema for personalized content."""
    chapter_id: str
    user_id: str
    personalized_content: str
    experience_level: str
    from_cache: bool


class ProfileAnalyzer:
    """Analyzes user profiles to determine content complexity level.

    Requirements: 7.1
    """

    # Experience level mappings
    EXPERIENCE_SCORES = {
        "beginner": 0,
        "intermediate": 1,
        "advanced": 2,
    }

    def __init__(self):
        """Initialize profile analyzer."""
        pass

    def analyze_profile(self, profile: UserProfile) -> ProfileAnalysisResult:
        """Analyze user profile to determine experience level.

        Args:
            profile: User profile data.

        Returns:
            ProfileAnalysisResult with experience level and analysis details.
        """
        # Check if profile has required data
        has_complete_profile = self._has_complete_profile(profile)

        # Calculate scores for each dimension
        software_score = self._get_experience_score(profile.software_experience)
        hardware_score = self._get_experience_score(profile.hardware_experience)
        domain_score = self._calculate_domain_score(profile)

        # Calculate overall experience level
        experience_level = self._determine_experience_level(
            software_score, hardware_score, domain_score, profile
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            profile, software_score, hardware_score, domain_score, experience_level
        )

        return ProfileAnalysisResult(
            experience_level=experience_level,
            has_complete_profile=has_complete_profile,
            software_score=software_score,
            hardware_score=hardware_score,
            domain_score=domain_score,
            reasoning=reasoning,
        )

    def _has_complete_profile(self, profile: UserProfile) -> bool:
        """Check if user has provided background information.

        Requirements: 7.3
        """
        return (
            profile.software_experience is not None
            or profile.hardware_experience is not None
            or (profile.programming_languages is not None and len(profile.programming_languages) > 0)
            or profile.robotics_experience
            or profile.ai_experience
        )

    def _get_experience_score(self, experience: Optional[str]) -> int:
        """Convert experience string to numeric score."""
        if experience is None:
            return 0  # Default to beginner if not specified
        return self.EXPERIENCE_SCORES.get(experience.lower(), 0)

    def _calculate_domain_score(self, profile: UserProfile) -> int:
        """Calculate domain-specific experience score.

        Based on robotics and AI experience flags.
        """
        score = 0
        if profile.robotics_experience:
            score += 1
        if profile.ai_experience:
            score += 1
        return score

    def _determine_experience_level(
        self,
        software_score: int,
        hardware_score: int,
        domain_score: int,
        profile: UserProfile,
    ) -> ExperienceLevel:
        """Determine overall experience level from individual scores.

        Weighting:
        - Software experience: 30%
        - Hardware experience: 30%
        - Domain experience (robotics/AI): 40%
        - Programming languages count: bonus factor
        """
        # Calculate weighted average (max possible = 2)
        weighted_score = (
            software_score * 0.3 +
            hardware_score * 0.3 +
            domain_score * 0.4  # domain_score max is 2
        )

        # Add bonus for programming language diversity
        if profile.programming_languages:
            lang_count = len(profile.programming_languages)
            if lang_count >= 5:
                weighted_score += 0.3
            elif lang_count >= 3:
                weighted_score += 0.2
            elif lang_count >= 1:
                weighted_score += 0.1

        # Determine level based on weighted score
        if weighted_score >= 1.5:
            return ExperienceLevel.ADVANCED
        elif weighted_score >= 0.7:
            return ExperienceLevel.INTERMEDIATE
        else:
            return ExperienceLevel.BEGINNER

    def _generate_reasoning(
        self,
        profile: UserProfile,
        software_score: int,
        hardware_score: int,
        domain_score: int,
        experience_level: ExperienceLevel,
    ) -> str:
        """Generate human-readable reasoning for the analysis."""
        parts = []

        if profile.software_experience:
            parts.append(f"software experience: {profile.software_experience}")
        if profile.hardware_experience:
            parts.append(f"hardware experience: {profile.hardware_experience}")
        if profile.programming_languages:
            parts.append(f"knows {len(profile.programming_languages)} programming language(s)")
        if profile.robotics_experience:
            parts.append("has robotics experience")
        if profile.ai_experience:
            parts.append("has AI experience")

        if not parts:
            return f"No background data provided, defaulting to {experience_level.value} level."

        return f"Based on {', '.join(parts)}, determined {experience_level.value} level."



class ContentAdapter:
    """Adapts content complexity using OpenAI while preserving technical terms.

    Requirements: 7.1, 7.2
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.7

    # Prompts for different experience levels
    ADAPTATION_PROMPTS = {
        ExperienceLevel.BEGINNER: """You are adapting educational content about Physical AI and Humanoid Robotics for a BEGINNER audience.

Guidelines:
1. Use simple, clear language and avoid jargon where possible
2. PRESERVE all technical terms exactly as written (e.g., "ROS", "SLAM", "inverse kinematics")
3. Add brief explanations or analogies for complex concepts
4. Include more context and background information
5. Use everyday analogies to explain abstract concepts
6. Break down complex processes into smaller, digestible steps
7. Maintain the original structure and all code examples
8. Keep all mathematical formulas but add intuitive explanations

The reader has limited programming experience and is new to robotics/AI.""",

        ExperienceLevel.INTERMEDIATE: """You are adapting educational content about Physical AI and Humanoid Robotics for an INTERMEDIATE audience.

Guidelines:
1. Use standard technical language appropriate for someone with programming experience
2. PRESERVE all technical terms exactly as written
3. Provide moderate explanations for advanced concepts
4. Include practical examples that connect to real-world applications
5. Maintain the original structure and all code examples
6. Assume familiarity with basic programming concepts
7. Add connections to related concepts when helpful

The reader has some programming experience and basic familiarity with robotics or AI concepts.""",

        ExperienceLevel.ADVANCED: """You are adapting educational content about Physical AI and Humanoid Robotics for an ADVANCED audience.

Guidelines:
1. Use precise technical language without unnecessary simplification
2. PRESERVE all technical terms exactly as written
3. Focus on nuances, edge cases, and advanced considerations
4. Include references to cutting-edge research or techniques when relevant
5. Maintain the original structure and all code examples
6. Assume strong familiarity with programming, mathematics, and domain concepts
7. Highlight optimization opportunities and best practices
8. Add depth to discussions of trade-offs and design decisions

The reader has extensive programming experience and solid background in robotics and/or AI.""",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """Initialize content adapter.

        Args:
            api_key: API key. Uses config settings if not provided.
            model: Model to use for adaptation.
            base_url: Base URL for API (used for Gemini compatibility).
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

    async def adapt_content(
        self,
        content: str,
        experience_level: ExperienceLevel,
    ) -> str:
        """Adapt content for the specified experience level.

        Args:
            content: Original content to adapt.
            experience_level: Target experience level.

        Returns:
            Adapted content string.
        """
        system_prompt = self.ADAPTATION_PROMPTS[experience_level]

        user_message = f"""Please adapt the following educational content for the specified audience level.
Maintain the same overall structure and preserve all technical terms, code blocks, and formulas.

ORIGINAL CONTENT:
{content}

ADAPTED CONTENT:"""

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

            adapted_content = response.choices[0].message.content or content
            logger.info(f"Content adapted for {experience_level.value} level")
            return adapted_content

        except Exception as e:
            logger.error(f"Content adaptation failed: {e}")
            raise

    async def close(self) -> None:
        """Close the OpenAI client."""
        await self._client.close()



class PersonalizationCache:
    """Manages caching of personalized content in PostgreSQL.

    Requirements: 7.4
    """

    async def get_cached_content(
        self,
        user_id: str,
        chapter_id: str,
    ) -> Optional[PersonalizedContentResponse]:
        """Retrieve cached personalized content.

        Args:
            user_id: User ID.
            chapter_id: Chapter ID.

        Returns:
            PersonalizedContentResponse if cached, None otherwise.
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.warning("Database pool not available for cache retrieval")
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT personalized_content, experience_level
                    FROM personalized_content
                    WHERE user_id = $1 AND chapter_id = $2
                    """,
                    uuid.UUID(user_id),
                    chapter_id,
                )

                if row:
                    logger.info(f"Cache hit for user {user_id}, chapter {chapter_id}")
                    return PersonalizedContentResponse(
                        chapter_id=chapter_id,
                        user_id=user_id,
                        personalized_content=row["personalized_content"],
                        experience_level=row["experience_level"] or "unknown",
                        from_cache=True,
                    )

                logger.debug(f"Cache miss for user {user_id}, chapter {chapter_id}")
                return None

        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    async def store_cached_content(
        self,
        user_id: str,
        chapter_id: str,
        personalized_content: str,
        experience_level: str,
    ) -> bool:
        """Store personalized content in cache.

        Uses upsert to handle both insert and update cases.

        Args:
            user_id: User ID.
            chapter_id: Chapter ID.
            personalized_content: The personalized content.
            experience_level: The experience level used for personalization.

        Returns:
            True if successful, False otherwise.
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.warning("Database pool not available for cache storage")
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO personalized_content
                        (id, user_id, chapter_id, personalized_content, experience_level)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id, chapter_id)
                    DO UPDATE SET
                        personalized_content = EXCLUDED.personalized_content,
                        experience_level = EXCLUDED.experience_level,
                        updated_at = NOW()
                    """,
                    uuid.uuid4(),
                    uuid.UUID(user_id),
                    chapter_id,
                    personalized_content,
                    experience_level,
                )

                logger.info(f"Cached content for user {user_id}, chapter {chapter_id}")
                return True

        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
            return False

    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cached content for a user.

        Called when user profile is updated.

        Args:
            user_id: User ID.

        Returns:
            Number of cache entries deleted.
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.warning("Database pool not available for cache invalidation")
            return 0

        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM personalized_content WHERE user_id = $1",
                    uuid.UUID(user_id),
                )

                deleted = int(result.split()[-1])
                if deleted > 0:
                    logger.info(f"Invalidated {deleted} cache entries for user {user_id}")
                return deleted

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0

    async def invalidate_chapter_cache(self, chapter_id: str) -> int:
        """Invalidate all cached content for a chapter.

        Called when chapter content is updated.

        Args:
            chapter_id: Chapter ID.

        Returns:
            Number of cache entries deleted.
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.warning("Database pool not available for cache invalidation")
            return 0

        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM personalized_content WHERE chapter_id = $1",
                    chapter_id,
                )

                deleted = int(result.split()[-1])
                if deleted > 0:
                    logger.info(f"Invalidated {deleted} cache entries for chapter {chapter_id}")
                return deleted

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0



class PersonalizationService:
    """Main service for content personalization.

    Orchestrates profile analysis, content adaptation, and caching.

    Requirements: 7.1, 7.2, 7.4
    """

    def __init__(
        self,
        profile_analyzer: Optional[ProfileAnalyzer] = None,
        content_adapter: Optional[ContentAdapter] = None,
        cache: Optional[PersonalizationCache] = None,
    ):
        """Initialize personalization service.

        Args:
            profile_analyzer: Profile analyzer instance.
            content_adapter: Content adapter instance.
            cache: Personalization cache instance.
        """
        self._profile_analyzer = profile_analyzer or ProfileAnalyzer()
        self._content_adapter = content_adapter or ContentAdapter()
        self._cache = cache or PersonalizationCache()

    @property
    def profile_analyzer(self) -> ProfileAnalyzer:
        """Get profile analyzer instance."""
        return self._profile_analyzer

    @property
    def content_adapter(self) -> ContentAdapter:
        """Get content adapter instance."""
        return self._content_adapter

    @property
    def cache(self) -> PersonalizationCache:
        """Get cache instance."""
        return self._cache

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Fetch user profile from database.

        Args:
            user_id: User ID.

        Returns:
            UserProfile if found, None otherwise.
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.warning("Database pool not available")
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, software_experience, hardware_experience,
                           programming_languages, robotics_experience, ai_experience
                    FROM users WHERE id = $1
                    """,
                    uuid.UUID(user_id),
                )

                if not row:
                    return None

                return UserProfile(
                    user_id=str(row["id"]),
                    software_experience=row["software_experience"],
                    hardware_experience=row["hardware_experience"],
                    programming_languages=row["programming_languages"],
                    robotics_experience=row["robotics_experience"],
                    ai_experience=row["ai_experience"],
                )

        except Exception as e:
            logger.error(f"Failed to fetch user profile: {e}")
            return None

    async def personalize_content(
        self,
        request: PersonalizedContentRequest,
    ) -> PersonalizedContentResponse:
        """Personalize content for a user.

        Flow:
        1. Check cache for existing personalized content
        2. If not cached, fetch user profile
        3. Analyze profile to determine experience level
        4. Adapt content using OpenAI
        5. Cache the result

        Args:
            request: Personalization request with chapter_id, user_id, and content.

        Returns:
            PersonalizedContentResponse with adapted content.

        Raises:
            ValueError: If user profile is incomplete (Requirements: 7.3)
        """
        # Step 1: Check cache
        cached = await self._cache.get_cached_content(
            request.user_id, request.chapter_id
        )
        if cached:
            return cached

        # Step 2: Fetch user profile
        profile = await self.get_user_profile(request.user_id)
        if not profile:
            raise ValueError(f"User not found: {request.user_id}")

        # Step 3: Analyze profile
        analysis = self._profile_analyzer.analyze_profile(profile)

        # Check for incomplete profile (Requirements: 7.3)
        if not analysis.has_complete_profile:
            raise ValueError(
                "User profile is incomplete. Please complete your background "
                "information before requesting personalized content."
            )

        logger.info(
            f"Personalizing content for user {request.user_id}: "
            f"{analysis.experience_level.value} level - {analysis.reasoning}"
        )

        # Step 4: Adapt content
        personalized_content = await self._content_adapter.adapt_content(
            request.original_content,
            analysis.experience_level,
        )

        # Step 5: Cache the result
        await self._cache.store_cached_content(
            request.user_id,
            request.chapter_id,
            personalized_content,
            analysis.experience_level.value,
        )

        return PersonalizedContentResponse(
            chapter_id=request.chapter_id,
            user_id=request.user_id,
            personalized_content=personalized_content,
            experience_level=analysis.experience_level.value,
            from_cache=False,
        )

    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate cache when user profile is updated.

        Args:
            user_id: User ID.

        Returns:
            Number of cache entries invalidated.
        """
        return await self._cache.invalidate_user_cache(user_id)

    async def close(self) -> None:
        """Close service resources."""
        await self._content_adapter.close()


# Global personalization service instance
_personalization_service: Optional[PersonalizationService] = None


def get_personalization_service() -> PersonalizationService:
    """Get the global personalization service instance."""
    global _personalization_service
    if _personalization_service is None:
        _personalization_service = PersonalizationService()
    return _personalization_service


async def close_personalization_service() -> None:
    """Close the global personalization service instance."""
    global _personalization_service
    if _personalization_service is not None:
        await _personalization_service.close()
        _personalization_service = None
