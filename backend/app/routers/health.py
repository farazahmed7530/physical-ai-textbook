"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint for deployment verification."""
    return {"status": "ready"}
