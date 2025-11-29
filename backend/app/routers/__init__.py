"""API Routers package."""

from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.health import router as health_router
from app.routers.personalize import router as personalize_router
from app.routers.translate import router as translate_router

__all__ = ["auth_router", "chat_router", "health_router", "personalize_router", "translate_router"]
