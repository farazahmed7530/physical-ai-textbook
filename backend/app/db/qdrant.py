"""Qdrant vector database connection and collection management."""

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class QdrantDatabase:
    """Qdrant vector database manager."""

    def __init__(self, settings: Settings):
        """Initialize Qdrant database manager with settings."""
        self.settings = settings
        self._client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        """Establish connection to Qdrant Cloud."""
        if not self.settings.has_qdrant_config:
            logger.warning("Qdrant URL not configured, skipping Qdrant connection")
            return

        try:
            self._client = AsyncQdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key if self.settings.qdrant_api_key else None,
                timeout=60,
            )
            logger.info("Qdrant client initialized")

            # Ensure collection exists
            await self._ensure_collection()
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def _ensure_collection(self) -> None:
        """Ensure the textbook content collection exists with proper configuration."""
        if not self._client:
            return

        collection_name = self.settings.qdrant_collection_name

        try:
            exists = await self._client.collection_exists(collection_name)

            if not exists:
                await self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.settings.qdrant_vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Qdrant client connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Qdrant client closed")

    async def health_check(self) -> dict:
        """Check Qdrant connection health."""
        result = {
            "status": "unhealthy",
            "connected": False,
            "collection_exists": False,
            "vectors_count": 0,
        }

        if not self.settings.has_qdrant_config:
            result["status"] = "not_configured"
            return result

        if self._client:
            try:
                # Check if collection exists and get info
                collection_name = self.settings.qdrant_collection_name
                exists = await self._client.collection_exists(collection_name)

                result["connected"] = True
                result["collection_exists"] = exists

                if exists:
                    collection_info = await self._client.get_collection(collection_name)
                    result["vectors_count"] = collection_info.vectors_count or 0
                    result["status"] = "healthy"
                else:
                    result["status"] = "collection_missing"
            except Exception as e:
                logger.error(f"Qdrant health check failed: {e}")
                result["error"] = str(e)

        return result

    async def upsert_vectors(
        self,
        points: list[dict[str, Any]],
    ) -> None:
        """Upsert vectors into the collection.

        Args:
            points: List of dicts with 'id', 'vector', and optional 'payload' keys.
        """
        if not self._client:
            raise RuntimeError("Qdrant not connected. Call connect() first.")

        qdrant_points = [
            models.PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload", {}),
            )
            for point in points
        ]

        await self._client.upsert(
            collection_name=self.settings.qdrant_collection_name,
            points=qdrant_points,
        )

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: The query embedding vector.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of search results with id, score, and payload.
        """
        if not self._client:
            raise RuntimeError("Qdrant not connected. Call connect() first.")

        results = await self._client.search(
            collection_name=self.settings.qdrant_collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            }
            for result in results
        ]

    async def delete_vectors(self, ids: list[str | int]) -> None:
        """Delete vectors by their IDs.

        Args:
            ids: List of vector IDs to delete.
        """
        if not self._client:
            raise RuntimeError("Qdrant not connected. Call connect() first.")

        await self._client.delete(
            collection_name=self.settings.qdrant_collection_name,
            points_selector=models.PointIdsList(points=ids),
        )

    @property
    def client(self) -> AsyncQdrantClient | None:
        """Get the Qdrant client."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Qdrant is connected."""
        return self._client is not None


# Global Qdrant instance
_qdrant_db: QdrantDatabase | None = None


async def init_qdrant() -> QdrantDatabase:
    """Initialize the global Qdrant database instance."""
    global _qdrant_db
    settings = get_settings()
    _qdrant_db = QdrantDatabase(settings)
    await _qdrant_db.connect()
    return _qdrant_db


async def close_qdrant() -> None:
    """Close the global Qdrant database instance."""
    global _qdrant_db
    if _qdrant_db:
        await _qdrant_db.disconnect()
        _qdrant_db = None


def get_qdrant_db() -> QdrantDatabase:
    """Get the global Qdrant database instance."""
    if _qdrant_db is None:
        raise RuntimeError("Qdrant database not initialized. Call init_qdrant() first.")
    return _qdrant_db


async def check_qdrant_health() -> dict:
    """Check Qdrant health status."""
    if _qdrant_db is None:
        return {"status": "not_initialized", "connected": False}
    return await _qdrant_db.health_check()
