"""Services package for business logic."""

from app.services.content_parser import (
    ContentParser,
    ContentChunker,
    ContentChunk,
    ContentMetadata,
    ParsedContent,
    parse_textbook_directory,
)
from app.services.context_builder import (
    ContextBuilder,
    BuiltContext,
    get_context_builder,
)
from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingResult,
    get_embedding_service,
    close_embedding_service,
)
from app.services.indexer_service import (
    QdrantIndexer,
    IndexingResult,
    IndexedChunk,
    get_indexer,
    index_textbook_content,
)
from app.services.query_processor import (
    QueryProcessor,
    ProcessedQuery,
    get_query_processor,
)
from app.services.rag_service import (
    RAGService,
    RAGRequest,
    RAGResponse,
    get_rag_service,
)
from app.services.response_generator import (
    ResponseGenerator,
    GeneratedResponse,
    Source,
    get_response_generator,
    close_response_generator,
)
from app.services.retriever_service import (
    VectorRetriever,
    RetrievedChunk,
    RetrievalResult,
    get_retriever,
)
from app.services.auth_service import (
    AuthService,
    UserCreate,
    UserLogin,
    UserResponse,
    UserBackground,
    AuthResponse,
    TokenResponse,
    get_auth_service,
)
from app.services.personalization_service import (
    PersonalizationService,
    ProfileAnalyzer,
    ContentAdapter,
    PersonalizationCache,
    ExperienceLevel,
    UserProfile,
    ProfileAnalysisResult,
    PersonalizedContentRequest,
    PersonalizedContentResponse,
    get_personalization_service,
    close_personalization_service,
)

__all__ = [
    # Content parser
    "ContentParser",
    "ContentChunker",
    "ContentChunk",
    "ContentMetadata",
    "ParsedContent",
    "parse_textbook_directory",
    # Context builder
    "ContextBuilder",
    "BuiltContext",
    "get_context_builder",
    # Embedding service
    "EmbeddingService",
    "EmbeddingResult",
    "get_embedding_service",
    "close_embedding_service",
    # Indexer service
    "QdrantIndexer",
    "IndexingResult",
    "IndexedChunk",
    "get_indexer",
    "index_textbook_content",
    # Query processor
    "QueryProcessor",
    "ProcessedQuery",
    "get_query_processor",
    # RAG service
    "RAGService",
    "RAGRequest",
    "RAGResponse",
    "get_rag_service",
    # Response generator
    "ResponseGenerator",
    "GeneratedResponse",
    "Source",
    "get_response_generator",
    "close_response_generator",
    # Retriever service
    "VectorRetriever",
    "RetrievedChunk",
    "RetrievalResult",
    "get_retriever",
    # Auth service
    "AuthService",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserBackground",
    "AuthResponse",
    "TokenResponse",
    "get_auth_service",
    # Personalization service
    "PersonalizationService",
    "ProfileAnalyzer",
    "ContentAdapter",
    "PersonalizationCache",
    "ExperienceLevel",
    "UserProfile",
    "ProfileAnalysisResult",
    "PersonalizedContentRequest",
    "PersonalizedContentResponse",
    "get_personalization_service",
    "close_personalization_service",
]
