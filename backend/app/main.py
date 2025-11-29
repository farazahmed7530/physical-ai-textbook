"""FastAPI application entry point with CORS and middleware configuration."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import auth_router, chat_router, health_router, personalize_router, translate_router
from app.db import init_postgres, close_postgres, init_qdrant, close_qdrant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database connections
    try:
        await init_postgres()
        logger.info("PostgreSQL connection initialized")
    except Exception as e:
        logger.warning(f"PostgreSQL initialization skipped or failed: {e}")

    try:
        await init_qdrant()
        logger.info("Qdrant connection initialized")
    except Exception as e:
        logger.warning(f"Qdrant initialization skipped or failed: {e}")

    yield

    # Close database connections
    logger.info("Shutting down application")
    await close_postgres()
    await close_qdrant()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for Physical AI & Humanoid Robotics textbook platform",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(personalize_router)
    app.include_router(translate_router)

    return app


app = create_app()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.perf_counter()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # Calculate processing time
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.4f}s"
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "type": "internal_error",
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
