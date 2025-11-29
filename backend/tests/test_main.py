"""Tests for main application."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_service import RAGResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rag_response():
    """Create a mock RAG response."""
    return RAGResponse(
        response="Physical AI refers to AI systems that interact with the physical world.",
        sources=[
            {
                "chapter_id": "intro",
                "section_title": "Introduction to Physical AI",
                "page_url": "/docs/intro",
                "relevance_score": 0.95,
            }
        ],
        is_fallback=False,
        query="What is Physical AI?",
        selected_text=None,
    )


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_check(client):
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_chat_endpoint_with_rag(mock_rag_response):
    """Test chat endpoint returns response from RAG pipeline."""
    from app.services.rag_service import get_rag_service

    # Create mock RAG service
    mock_service = AsyncMock()
    mock_service.process_query = AsyncMock(return_value=mock_rag_response)

    # Override the dependency
    app.dependency_overrides[get_rag_service] = lambda: mock_service

    try:
        client = TestClient(app)
        response = client.post(
            "/api/chat",
            json={"query": "What is Physical AI?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert "is_fallback" in data
        assert data["response"] == mock_rag_response.response
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chapter_id"] == "intro"
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_cors_headers(client):
    """Test CORS headers are present in response."""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS preflight should succeed
    assert response.status_code == 200


def test_process_time_header(client):
    """Test X-Process-Time header is added to responses."""
    response = client.get("/")
    assert "X-Process-Time" in response.headers


def test_chat_endpoint_validation_error(client):
    """Test chat endpoint returns 422 for invalid input."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
