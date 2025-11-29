"""PostgreSQL database connection with asyncpg and SQLAlchemy async support."""

import logging
from typing import AsyncGenerator

import asyncpg
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class PostgresDatabase:
    """PostgreSQL database manager with connection pooling."""

    def __init__(self, settings: Settings):
        """Initialize database manager with settings."""
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Establish database connection with connection pooling."""
        if not self.settings.has_database_config:
            logger.warning("Database URL not configured, skipping PostgreSQL connection")
            return

        try:
            # Create SQLAlchemy async engine
            self._engine = create_async_engine(
                self.settings.database_url,
                pool_size=self.settings.db_pool_min_size,
                max_overflow=self.settings.db_pool_max_size - self.settings.db_pool_min_size,
                pool_pre_ping=True,
                echo=self.settings.debug,
            )

            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            # Also create raw asyncpg pool for direct queries if needed
            # Extract connection params from URL for asyncpg pool
            self._pool = await asyncpg.create_pool(
                dsn=self.settings.database_url.replace("+asyncpg", ""),
                min_size=self.settings.db_pool_min_size,
                max_size=self.settings.db_pool_max_size,
                command_timeout=self.settings.db_command_timeout,
            )

            logger.info("PostgreSQL connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self) -> None:
        """Close database connections."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("asyncpg connection pool closed")

        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("SQLAlchemy engine disposed")

    async def health_check(self) -> dict:
        """Check database connection health."""
        result = {
            "status": "unhealthy",
            "connected": False,
            "pool_size": 0,
            "pool_idle": 0,
        }

        if not self.settings.has_database_config:
            result["status"] = "not_configured"
            return result

        if self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                result["status"] = "healthy"
                result["connected"] = True
                result["pool_size"] = self._pool.get_size()
                result["pool_idle"] = self._pool.get_idle_size()
            except Exception as e:
                logger.error(f"PostgreSQL health check failed: {e}")
                result["error"] = str(e)

        return result

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async session from the session factory."""
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @property
    def pool(self) -> asyncpg.Pool | None:
        """Get the raw asyncpg connection pool."""
        return self._pool

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the SQLAlchemy async engine."""
        return self._engine

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._engine is not None and self._pool is not None


# Global database instance
_postgres_db: PostgresDatabase | None = None


async def init_postgres() -> PostgresDatabase:
    """Initialize the global PostgreSQL database instance."""
    global _postgres_db
    settings = get_settings()
    _postgres_db = PostgresDatabase(settings)
    await _postgres_db.connect()
    return _postgres_db


async def close_postgres() -> None:
    """Close the global PostgreSQL database instance."""
    global _postgres_db
    if _postgres_db:
        await _postgres_db.disconnect()
        _postgres_db = None


def get_postgres_db() -> PostgresDatabase:
    """Get the global PostgreSQL database instance."""
    if _postgres_db is None:
        raise RuntimeError("PostgreSQL database not initialized. Call init_postgres() first.")
    return _postgres_db


async def check_postgres_health() -> dict:
    """Check PostgreSQL health status."""
    if _postgres_db is None:
        return {"status": "not_initialized", "connected": False}
    return await _postgres_db.health_check()
