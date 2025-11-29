"""Tests for database connection modules."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.db.postgres import PostgresDatabase, check_postgres_health
from app.db.qdrant import QdrantDatabase, check_qdrant_health


class TestPostgresDatabase:
    """Tests for PostgresDatabase class."""

    def test_init_with_settings(self):
        """Test PostgresDatabase initialization with settings."""
        settings = Settings(database_url="postgresql+asyncpg://test:test@localhost/test")
        db = PostgresDatabase(settings)

        assert db.settings == settings
        assert db._engine is None
        assert db._pool is None
        assert not db.is_connected

    def test_has_database_config_true(self):
        """Test has_database_config returns True when URL is set."""
        settings = Settings(database_url="postgresql+asyncpg://test:test@localhost/test")
        assert settings.has_database_config is True

    def test_has_database_config_false(self):
        """Test has_database_config returns False when URL is empty."""
        settings = Settings(database_url="")
        assert settings.has_database_config is False

    @pytest.mark.asyncio
    async def test_connect_skips_when_no_config(self):
        """Test connect skips when database URL is not configured."""
        settings = Settings(database_url="")
        db = PostgresDatabase(settings)

        await db.connect()

        assert db._engine is None
        assert db._pool is None

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        """Test health check returns not_configured when URL is empty."""
        settings = Settings(database_url="")
        db = PostgresDatabase(settings)

        result = await db.health_check()

        assert result["status"] == "not_configured"
        assert result["connected"] is False


class TestQdrantDatabase:
    """Tests for QdrantDatabase class."""

    def test_init_with_settings(self):
        """Test QdrantDatabase initialization with settings."""
        settings = Settings(qdrant_url="https://test.qdrant.io", qdrant_api_key="test-key")
        db = QdrantDatabase(settings)

        assert db.settings == settings
        assert db._client is None
        assert not db.is_connected

    def test_has_qdrant_config_true(self):
        """Test has_qdrant_config returns True when URL is set."""
        settings = Settings(qdrant_url="https://test.qdrant.io")
        assert settings.has_qdrant_config is True

    def test_has_qdrant_config_false(self):
        """Test has_qdrant_config returns False when URL is empty."""
        settings = Settings(qdrant_url="")
        assert settings.has_qdrant_config is False

    @pytest.mark.asyncio
    async def test_connect_skips_when_no_config(self):
        """Test connect skips when Qdrant URL is not configured."""
        settings = Settings(qdrant_url="")
        db = QdrantDatabase(settings)

        await db.connect()

        assert db._client is None

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        """Test health check returns not_configured when URL is empty."""
        settings = Settings(qdrant_url="")
        db = QdrantDatabase(settings)

        result = await db.health_check()

        assert result["status"] == "not_configured"
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_upsert_raises_when_not_connected(self):
        """Test upsert raises error when not connected."""
        settings = Settings(qdrant_url="")
        db = QdrantDatabase(settings)

        with pytest.raises(RuntimeError, match="Qdrant not connected"):
            await db.upsert_vectors([{"id": 1, "vector": [0.1] * 1536}])

    @pytest.mark.asyncio
    async def test_search_raises_when_not_connected(self):
        """Test search raises error when not connected."""
        settings = Settings(qdrant_url="")
        db = QdrantDatabase(settings)

        with pytest.raises(RuntimeError, match="Qdrant not connected"):
            await db.search([0.1] * 1536)


class TestGlobalFunctions:
    """Tests for global database functions."""

    @pytest.mark.asyncio
    async def test_check_postgres_health_not_initialized(self):
        """Test check_postgres_health when not initialized."""
        # Reset global state
        import app.db.postgres as pg_module
        pg_module._postgres_db = None

        result = await check_postgres_health()

        assert result["status"] == "not_initialized"
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_check_qdrant_health_not_initialized(self):
        """Test check_qdrant_health when not initialized."""
        # Reset global state
        import app.db.qdrant as qd_module
        qd_module._qdrant_db = None

        result = await check_qdrant_health()

        assert result["status"] == "not_initialized"
        assert result["connected"] is False
