"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Application
    app_name: str = "Physical AI Textbook API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Database (Neon PostgreSQL)
    database_url: str = ""
    db_pool_min_size: int = 5
    db_pool_max_size: int = 20
    db_command_timeout: int = 60

    # Qdrant Cloud
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "textbook_content"
    qdrant_vector_size: int = 768  # Gemini text-embedding-004 dimensions (OpenAI uses 1536)

    # LLM Provider Configuration
    # Supported providers: "openai", "gemini"
    llm_provider: str = "openai"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # Gemini Configuration (uses OpenAI-compatible endpoint)
    # Get free API key at: https://aistudio.google.com/apikey
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_chat_model: str = "gemini-2.0-flash"  # Latest free model
    gemini_embedding_model: str = "text-embedding-004"

    # Authentication (JWT)
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    session_expire_days: int = 7

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def has_database_config(self) -> bool:
        """Check if database configuration is provided."""
        return bool(self.database_url)

    @property
    def has_qdrant_config(self) -> bool:
        """Check if Qdrant configuration is provided."""
        return bool(self.qdrant_url)

    @property
    def has_llm_config(self) -> bool:
        """Check if LLM configuration is provided."""
        if self.llm_provider == "gemini":
            return bool(self.gemini_api_key)
        return bool(self.openai_api_key)

    @property
    def active_api_key(self) -> str:
        """Get the active API key based on provider."""
        if self.llm_provider == "gemini":
            return self.gemini_api_key
        return self.openai_api_key

    @property
    def active_base_url(self) -> str | None:
        """Get the active base URL based on provider."""
        if self.llm_provider == "gemini":
            return self.gemini_base_url
        return None  # OpenAI uses default

    @property
    def active_chat_model(self) -> str:
        """Get the active chat model based on provider."""
        if self.llm_provider == "gemini":
            return self.gemini_chat_model
        return self.openai_chat_model

    @property
    def active_embedding_model(self) -> str:
        """Get the active embedding model based on provider."""
        if self.llm_provider == "gemini":
            return self.gemini_embedding_model
        return self.openai_embedding_model


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
