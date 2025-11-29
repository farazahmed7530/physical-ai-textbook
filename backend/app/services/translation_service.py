"""Translation service for converting content to Urdu.

This module provides functionality to:
- Translate content to Urdu using OpenAI
- Preserve technical terms with transliteration
- Cache translated content in PostgreSQL
- Apply RTL formatting for Urdu text

Requirements: 8.1, 8.2, 8.3, 8.4
"""

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings
from app.db.postgres import get_postgres_db

logger = logging.getLogger(__name__)


class TranslationRequest(BaseModel):
    """Request schema for content translation."""
    chapter_id: str
    content: str
    language: str = "ur"  # Default to Urdu


class TranslationResponse(BaseModel):
    """Response schema for translated content."""
    chapter_id: str
    translated_content: str
    language: str
    from_cache: bool
    has_rtl_formatting: bool


@dataclass
class TechnicalTerm:
    """Represents a technical term with its transliteration."""
    original: str
    transliteration: str
    position: int


class TechnicalTermHandler:
    """Handles preservation and transliteration of technical terms.

    Requirements: 8.2
    """

    # Common technical terms in Physical AI/Robotics that should be preserved
    # with their Urdu transliterations
    TECHNICAL_TERMS = {
        # Robotics terms
        "robot": "روبوٹ",
        "robotics": "روبوٹکس",
        "humanoid": "ہیومنائیڈ",
        "actuator": "ایکچویٹر",
        "sensor": "سینسر",
        "servo": "سروو",
        "motor": "موٹر",
        "encoder": "انکوڈر",
        "gripper": "گرپر",
        "manipulator": "مینیپولیٹر",
        "end-effector": "اینڈ ایفیکٹر",
        "joint": "جوائنٹ",
        "link": "لنک",
        "DOF": "DOF",
        "degrees of freedom": "ڈگریز آف فریڈم",

        # AI/ML terms
        "AI": "AI",
        "artificial intelligence": "آرٹیفیشل انٹیلیجنس",
        "machine learning": "مشین لرننگ",
        "deep learning": "ڈیپ لرننگ",
        "neural network": "نیورل نیٹ ورک",
        "CNN": "CNN",
        "RNN": "RNN",
        "LSTM": "LSTM",
        "transformer": "ٹرانسفارمر",
        "reinforcement learning": "رینفورسمنٹ لرننگ",
        "supervised learning": "سپروائزڈ لرننگ",
        "unsupervised learning": "ان سپروائزڈ لرننگ",
        "model": "ماڈل",
        "training": "ٹریننگ",
        "inference": "انفرنس",
        "dataset": "ڈیٹاسیٹ",
        "epoch": "ایپاک",
        "batch": "بیچ",
        "gradient": "گریڈینٹ",
        "backpropagation": "بیک پروپیگیشن",
        "optimizer": "آپٹیمائزر",
        "loss function": "لاس فنکشن",

        # Computer Vision terms
        "computer vision": "کمپیوٹر ویژن",
        "image processing": "امیج پروسیسنگ",
        "object detection": "آبجیکٹ ڈیٹیکشن",
        "segmentation": "سیگمینٹیشن",
        "SLAM": "SLAM",
        "lidar": "لائیڈار",
        "camera": "کیمرہ",
        "depth sensor": "ڈیپتھ سینسر",
        "point cloud": "پوائنٹ کلاؤڈ",
        "feature extraction": "فیچر ایکسٹریکشن",

        # Motion Planning terms
        "motion planning": "موشن پلاننگ",
        "path planning": "پاتھ پلاننگ",
        "trajectory": "ٹریجیکٹری",
        "kinematics": "کائنیمیٹکس",
        "inverse kinematics": "انورس کائنیمیٹکس",
        "forward kinematics": "فارورڈ کائنیمیٹکس",
        "dynamics": "ڈائنامکس",
        "control": "کنٹرول",
        "PID": "PID",
        "feedback": "فیڈبیک",
        "state estimation": "سٹیٹ ایسٹیمیشن",

        # NLP terms
        "NLP": "NLP",
        "natural language processing": "نیچرل لینگویج پروسیسنگ",
        "tokenization": "ٹوکنائزیشن",
        "embedding": "ایمبیڈنگ",
        "attention": "اٹینشن",
        "LLM": "LLM",
        "large language model": "لارج لینگویج ماڈل",

        # Programming terms
        "Python": "پائتھون",
        "ROS": "ROS",
        "API": "API",
        "SDK": "SDK",
        "framework": "فریم ورک",
        "library": "لائبریری",
        "function": "فنکشن",
        "class": "کلاس",
        "object": "آبجیکٹ",
        "variable": "ویری ایبل",
        "algorithm": "الگورتھم",
        "data structure": "ڈیٹا سٹرکچر",
        "array": "ارے",
        "matrix": "میٹرکس",
        "tensor": "ٹینسر",
    }

    def __init__(self):
        """Initialize technical term handler."""
        # Create case-insensitive lookup
        self._term_lookup = {k.lower(): v for k, v in self.TECHNICAL_TERMS.items()}

    def get_transliteration(self, term: str) -> Optional[str]:
        """Get Urdu transliteration for a technical term.

        Args:
            term: The technical term to transliterate.

        Returns:
            Urdu transliteration if found, None otherwise.
        """
        return self._term_lookup.get(term.lower())

    def extract_technical_terms(self, content: str) -> list[TechnicalTerm]:
        """Extract technical terms from content.

        Args:
            content: The content to analyze.

        Returns:
            List of TechnicalTerm objects found in the content.
        """
        terms = []
        content_lower = content.lower()

        for term, transliteration in self.TECHNICAL_TERMS.items():
            # Find all occurrences of the term
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(content):
                terms.append(TechnicalTerm(
                    original=match.group(),
                    transliteration=transliteration,
                    position=match.start(),
                ))

        # Sort by position
        terms.sort(key=lambda t: t.position)
        return terms

    def create_term_glossary(self, content: str) -> str:
        """Create a glossary of technical terms found in content.

        Args:
            content: The content to analyze.

        Returns:
            Formatted glossary string for use in translation prompts.
        """
        terms = self.extract_technical_terms(content)
        if not terms:
            return ""

        # Deduplicate terms
        seen = set()
        unique_terms = []
        for term in terms:
            key = term.original.lower()
            if key not in seen:
                seen.add(key)
                unique_terms.append(term)

        glossary_lines = ["Technical Terms Glossary:"]
        for term in unique_terms:
            glossary_lines.append(f"- {term.original} → {term.transliteration}")

        return "\n".join(glossary_lines)


class TranslationEngine:
    """Translates content to Urdu using OpenAI.

    Requirements: 8.1, 8.2
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS = 8192
    DEFAULT_TEMPERATURE = 0.3  # Lower temperature for more consistent translations

    SYSTEM_PROMPT = """You are an expert translator specializing in technical and educational content translation from English to Urdu.

Your task is to translate the provided educational content about Physical AI and Humanoid Robotics into Urdu while following these guidelines:

1. PRESERVE TECHNICAL TERMS: Keep technical terms in their original English form OR use the provided Urdu transliteration. Do NOT translate technical terms into descriptive Urdu phrases.

2. MAINTAIN STRUCTURE: Preserve all markdown formatting, code blocks, headers, lists, and other structural elements exactly as they appear.

3. CODE BLOCKS: Do NOT translate content inside code blocks (```). Keep all code, variable names, and comments in English.

4. MATHEMATICAL FORMULAS: Keep mathematical notation and formulas unchanged.

5. NATURAL URDU: Write in natural, fluent Urdu that reads well for native speakers. Avoid overly literal translations.

6. EDUCATIONAL TONE: Maintain the educational and instructional tone of the original content.

7. CONSISTENCY: Use consistent terminology throughout the translation.

8. LINKS AND REFERENCES: Keep URLs and file paths unchanged.

The translation should be suitable for Urdu-speaking students learning about Physical AI and Robotics."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """Initialize translation engine.

        Args:
            api_key: API key. Uses config settings if not provided.
            model: Model to use for translation.
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

        self._term_handler = TechnicalTermHandler()

    async def translate_to_urdu(self, content: str) -> str:
        """Translate content to Urdu.

        Args:
            content: Original English content to translate.

        Returns:
            Translated Urdu content.

        Requirements: 8.1, 8.2
        """
        # Create glossary of technical terms
        glossary = self._term_handler.create_term_glossary(content)

        # Build user message with glossary
        user_message_parts = []
        if glossary:
            user_message_parts.append(glossary)
            user_message_parts.append("\n---\n")

        user_message_parts.append("Please translate the following content to Urdu:\n\n")
        user_message_parts.append(content)

        user_message = "".join(user_message_parts)

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            translated_content = response.choices[0].message.content or content
            logger.info("Content translated to Urdu successfully")
            return translated_content

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    async def close(self) -> None:
        """Close the OpenAI client."""
        await self._client.close()


class RTLFormatter:
    """Applies right-to-left formatting for Urdu content.

    Requirements: 8.3
    """

    # CSS class for RTL content
    RTL_WRAPPER_CLASS = "rtl-content"

    # Patterns for content that should remain LTR
    LTR_PATTERNS = [
        r'```[\s\S]*?```',  # Code blocks
        r'`[^`]+`',         # Inline code
        r'\$\$[\s\S]*?\$\$',  # Math blocks
        r'\$[^$]+\$',       # Inline math
        r'https?://[^\s]+',  # URLs
        r'\[[^\]]+\]\([^)]+\)',  # Markdown links
    ]

    def __init__(self):
        """Initialize RTL formatter."""
        self._ltr_pattern = re.compile('|'.join(self.LTR_PATTERNS))

    def apply_rtl_formatting(self, content: str) -> str:
        """Apply RTL formatting to translated content.

        Wraps the content with RTL direction markers while preserving
        LTR formatting for code blocks and other technical content.

        Args:
            content: Translated Urdu content.

        Returns:
            Content with RTL formatting applied.

        Requirements: 8.3
        """
        # Add RTL wrapper div
        formatted_content = f'<div class="{self.RTL_WRAPPER_CLASS}" dir="rtl">\n\n{content}\n\n</div>'
        return formatted_content

    def wrap_ltr_content(self, content: str) -> str:
        """Wrap LTR content (code blocks, etc.) with explicit LTR markers.

        Args:
            content: Content that may contain mixed LTR/RTL sections.

        Returns:
            Content with LTR sections properly marked.
        """
        def wrap_match(match):
            return f'<span dir="ltr">{match.group()}</span>'

        return self._ltr_pattern.sub(wrap_match, content)

    def get_rtl_css(self) -> str:
        """Get CSS styles for RTL content.

        Returns:
            CSS string for RTL formatting.

        Requirements: 8.3
        """
        return """
.rtl-content {
    direction: rtl;
    text-align: right;
    font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif;
    line-height: 1.8;
}

.rtl-content code,
.rtl-content pre {
    direction: ltr;
    text-align: left;
    font-family: 'Fira Code', 'Consolas', monospace;
}

.rtl-content pre {
    overflow-x: auto;
}

.rtl-content h1,
.rtl-content h2,
.rtl-content h3,
.rtl-content h4,
.rtl-content h5,
.rtl-content h6 {
    text-align: right;
}

.rtl-content ul,
.rtl-content ol {
    padding-right: 2em;
    padding-left: 0;
}

.rtl-content li {
    text-align: right;
}

.rtl-content table {
    direction: rtl;
}

.rtl-content th,
.rtl-content td {
    text-align: right;
}

.rtl-content blockquote {
    border-right: 4px solid #ccc;
    border-left: none;
    padding-right: 1em;
    padding-left: 0;
    margin-right: 0;
}

.rtl-content .math,
.rtl-content .katex {
    direction: ltr;
}
"""

    def has_urdu_content(self, content: str) -> bool:
        """Check if content contains Urdu script characters.

        Args:
            content: Content to check.

        Returns:
            True if content contains Urdu characters.

        Requirements: 8.1
        """
        # Urdu Unicode range: 0600-06FF (Arabic script used for Urdu)
        urdu_pattern = re.compile(r'[\u0600-\u06FF]')
        return bool(urdu_pattern.search(content))


class TranslationCache:
    """Manages caching of translated content in PostgreSQL.

    Requirements: 8.4
    """

    async def get_cached_translation(
        self,
        chapter_id: str,
        language: str = "ur",
    ) -> Optional[TranslationResponse]:
        """Retrieve cached translated content.

        Args:
            chapter_id: Chapter ID.
            language: Target language code.

        Returns:
            TranslationResponse if cached, None otherwise.
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
                    SELECT translated_content, language
                    FROM translated_content
                    WHERE chapter_id = $1 AND language = $2
                    """,
                    chapter_id,
                    language,
                )

                if row:
                    logger.info(f"Cache hit for chapter {chapter_id}, language {language}")
                    return TranslationResponse(
                        chapter_id=chapter_id,
                        translated_content=row["translated_content"],
                        language=row["language"],
                        from_cache=True,
                        has_rtl_formatting=True,
                    )

                logger.debug(f"Cache miss for chapter {chapter_id}, language {language}")
                return None

        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    async def store_cached_translation(
        self,
        chapter_id: str,
        translated_content: str,
        language: str = "ur",
    ) -> bool:
        """Store translated content in cache.

        Uses upsert to handle both insert and update cases.

        Args:
            chapter_id: Chapter ID.
            translated_content: The translated content.
            language: Target language code.

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
                    INSERT INTO translated_content
                        (id, chapter_id, translated_content, language)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (chapter_id, language)
                    DO UPDATE SET
                        translated_content = EXCLUDED.translated_content,
                        updated_at = NOW()
                    """,
                    uuid.uuid4(),
                    chapter_id,
                    translated_content,
                    language,
                )

                logger.info(f"Cached translation for chapter {chapter_id}, language {language}")
                return True

        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
            return False

    async def invalidate_chapter_cache(
        self,
        chapter_id: str,
        language: Optional[str] = None,
    ) -> int:
        """Invalidate cached translations for a chapter.

        Args:
            chapter_id: Chapter ID.
            language: Optional language to invalidate. If None, invalidates all languages.

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
                if language:
                    result = await conn.execute(
                        "DELETE FROM translated_content WHERE chapter_id = $1 AND language = $2",
                        chapter_id,
                        language,
                    )
                else:
                    result = await conn.execute(
                        "DELETE FROM translated_content WHERE chapter_id = $1",
                        chapter_id,
                    )

                deleted = int(result.split()[-1])
                if deleted > 0:
                    logger.info(f"Invalidated {deleted} cache entries for chapter {chapter_id}")
                return deleted

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0


class TranslationService:
    """Main service for content translation.

    Orchestrates translation engine, RTL formatting, and caching.

    Requirements: 8.1, 8.2, 8.3, 8.4
    """

    def __init__(
        self,
        translation_engine: Optional[TranslationEngine] = None,
        rtl_formatter: Optional[RTLFormatter] = None,
        cache: Optional[TranslationCache] = None,
    ):
        """Initialize translation service.

        Args:
            translation_engine: Translation engine instance.
            rtl_formatter: RTL formatter instance.
            cache: Translation cache instance.
        """
        self._translation_engine = translation_engine or TranslationEngine()
        self._rtl_formatter = rtl_formatter or RTLFormatter()
        self._cache = cache or TranslationCache()

    @property
    def translation_engine(self) -> TranslationEngine:
        """Get translation engine instance."""
        return self._translation_engine

    @property
    def rtl_formatter(self) -> RTLFormatter:
        """Get RTL formatter instance."""
        return self._rtl_formatter

    @property
    def cache(self) -> TranslationCache:
        """Get cache instance."""
        return self._cache

    async def translate_content(
        self,
        request: TranslationRequest,
    ) -> TranslationResponse:
        """Translate content to the target language.

        Flow:
        1. Check cache for existing translation
        2. If not cached, translate using OpenAI
        3. Apply RTL formatting for Urdu
        4. Cache the result

        Args:
            request: Translation request with chapter_id and content.

        Returns:
            TranslationResponse with translated content.

        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        # Step 1: Check cache
        cached = await self._cache.get_cached_translation(
            request.chapter_id, request.language
        )
        if cached:
            return cached

        # Step 2: Translate content
        logger.info(f"Translating chapter {request.chapter_id} to {request.language}")
        translated_content = await self._translation_engine.translate_to_urdu(
            request.content
        )

        # Step 3: Apply RTL formatting for Urdu
        if request.language == "ur":
            translated_content = self._rtl_formatter.apply_rtl_formatting(
                translated_content
            )

        # Step 4: Cache the result
        await self._cache.store_cached_translation(
            request.chapter_id,
            translated_content,
            request.language,
        )

        return TranslationResponse(
            chapter_id=request.chapter_id,
            translated_content=translated_content,
            language=request.language,
            from_cache=False,
            has_rtl_formatting=request.language == "ur",
        )

    async def invalidate_chapter_cache(
        self,
        chapter_id: str,
        language: Optional[str] = None,
    ) -> int:
        """Invalidate cache when chapter content is updated.

        Args:
            chapter_id: Chapter ID.
            language: Optional specific language to invalidate.

        Returns:
            Number of cache entries invalidated.
        """
        return await self._cache.invalidate_chapter_cache(chapter_id, language)

    def get_rtl_css(self) -> str:
        """Get CSS styles for RTL content.

        Returns:
            CSS string for RTL formatting.
        """
        return self._rtl_formatter.get_rtl_css()

    async def close(self) -> None:
        """Close service resources."""
        await self._translation_engine.close()


# Global translation service instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get the global translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


async def close_translation_service() -> None:
    """Close the global translation service instance."""
    global _translation_service
    if _translation_service is not None:
        await _translation_service.close()
        _translation_service = None
