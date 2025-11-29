"""Query processor for RAG retrieval pipeline.

This module provides functionality to:
- Preprocess user queries for embedding
- Handle query expansion for better retrieval
- Generate query embeddings

Requirements: 4.2
"""

import logging
import re
from dataclasses import dataclass

from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingResult,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessedQuery:
    """Result of query processing."""

    original_query: str
    processed_query: str
    expanded_terms: list[str]
    embedding: list[float]


class QueryProcessor:
    """Service for preprocessing and embedding user queries."""

    # Common stop words to filter out for expansion
    STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once", "here",
        "there", "when", "where", "why", "how", "all", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
        "because", "until", "while", "what", "which", "who", "whom", "this",
        "that", "these", "those", "am", "i", "me", "my", "myself", "we", "our",
        "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
        "he", "him", "his", "himself", "she", "her", "hers", "herself", "it",
        "its", "itself", "they", "them", "their", "theirs", "themselves",
    }

    # Domain-specific synonyms for query expansion
    DOMAIN_SYNONYMS = {
        "robot": ["robotics", "robotic", "humanoid"],
        "ai": ["artificial intelligence", "machine learning", "ml"],
        "vision": ["computer vision", "visual perception", "image processing"],
        "motion": ["movement", "locomotion", "kinematics"],
        "sensor": ["sensors", "perception", "sensing"],
        "control": ["controller", "controlling", "actuation"],
        "learning": ["training", "machine learning", "neural network"],
        "planning": ["path planning", "motion planning", "trajectory"],
        "manipulation": ["grasping", "handling", "pick and place"],
        "navigation": ["localization", "mapping", "slam"],
        "hri": ["human robot interaction", "human-robot interaction"],
        "safety": ["safe", "collision avoidance", "risk"],
        "ethics": ["ethical", "responsible ai", "fairness"],
    }

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        enable_expansion: bool = True,
    ):
        """Initialize query processor.

        Args:
            embedding_service: Embedding service instance. Uses global if not provided.
            enable_expansion: Whether to enable query expansion.
        """
        self._embedding_service = embedding_service
        self.enable_expansion = enable_expansion

    @property
    def embedding_service(self) -> EmbeddingService:
        """Get embedding service instance."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    def preprocess_query(self, query: str) -> str:
        """Preprocess a query for better retrieval.

        Args:
            query: Raw user query.

        Returns:
            Preprocessed query string.
        """
        # Normalize whitespace
        processed = " ".join(query.split())

        # Convert to lowercase for consistency
        processed = processed.lower()

        # Remove excessive punctuation but keep question marks
        processed = re.sub(r"[^\w\s\?\-]", " ", processed)

        # Normalize whitespace again after punctuation removal
        processed = " ".join(processed.split())

        return processed

    def expand_query(self, query: str) -> list[str]:
        """Expand query with domain-specific synonyms.

        Args:
            query: Preprocessed query string.

        Returns:
            List of expansion terms.
        """
        if not self.enable_expansion:
            return []

        expanded_terms = []
        query_lower = query.lower()
        words = set(query_lower.split())

        # Remove stop words from consideration
        meaningful_words = words - self.STOP_WORDS

        # Find synonyms for meaningful words
        for word in meaningful_words:
            if word in self.DOMAIN_SYNONYMS:
                for synonym in self.DOMAIN_SYNONYMS[word]:
                    if synonym.lower() not in query_lower:
                        expanded_terms.append(synonym)

        return expanded_terms

    def build_embedding_text(
        self,
        processed_query: str,
        expanded_terms: list[str],
    ) -> str:
        """Build the text to embed from query and expansions.

        Args:
            processed_query: The preprocessed query.
            expanded_terms: List of expansion terms.

        Returns:
            Combined text for embedding.
        """
        # Start with the processed query
        parts = [processed_query]

        # Add expanded terms if any
        if expanded_terms:
            # Add a subset of most relevant expansions
            relevant_expansions = expanded_terms[:3]  # Limit to avoid noise
            parts.append(" ".join(relevant_expansions))

        return " ".join(parts)

    async def process_query(self, query: str) -> ProcessedQuery:
        """Process a query and generate its embedding.

        Args:
            query: Raw user query.

        Returns:
            ProcessedQuery with embedding and metadata.
        """
        logger.debug(f"Processing query: {query[:100]}...")

        # Preprocess the query
        processed = self.preprocess_query(query)

        # Expand with synonyms
        expanded_terms = self.expand_query(processed)

        # Build text for embedding
        embedding_text = self.build_embedding_text(processed, expanded_terms)

        # Generate embedding
        embedding_result = await self.embedding_service.generate_embedding(
            embedding_text
        )

        logger.debug(
            f"Query processed: {len(expanded_terms)} expansions, "
            f"embedding dim: {len(embedding_result.embedding)}"
        )

        return ProcessedQuery(
            original_query=query,
            processed_query=processed,
            expanded_terms=expanded_terms,
            embedding=embedding_result.embedding,
        )


# Global query processor instance
_query_processor: QueryProcessor | None = None


def get_query_processor() -> QueryProcessor:
    """Get the global query processor instance."""
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessor()
    return _query_processor
