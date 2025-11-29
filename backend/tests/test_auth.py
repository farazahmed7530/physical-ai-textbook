"""Tests for authentication endpoints.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt

from app.main import app
from app.services.auth_service import (
    AuthService,
    UserCreate,
    UserLogin,
    UserBackground,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_pool():
    """Create a mock database pool."""
    pool = MagicMock()
    return pool


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hash_is_different_from_plain(self):
        """Password hash should be different from plain password."""
        password = "test_password_123"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        assert hashed.decode('utf-8') != password

    def test_password_verification_works(self):
        """Password verification should work correctly."""
        password = "test_password_123"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        assert bcrypt.checkpw(password.encode('utf-8'), hashed) is True

    def test_wrong_password_fails_verification(self):
        """Wrong password should fail verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        assert bcrypt.checkpw(wrong_password.encode('utf-8'), hashed) is False


class TestAuthService:
    """Test AuthService methods."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        auth_service = AuthService()
        user_id = str(uuid.uuid4())

        token, expires_at = auth_service.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert expires_at > datetime.now(timezone.utc)

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        auth_service = AuthService()
        user_id = str(uuid.uuid4())

        token, _ = auth_service.create_access_token(user_id)
        payload = auth_service.decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        auth_service = AuthService()

        payload = auth_service.decode_token("invalid_token")

        assert payload is None

    def test_hash_password(self):
        """Test password hashing."""
        auth_service = AuthService()
        password = "secure_password_123"

        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        auth_service = AuthService()
        password = "secure_password_123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        auth_service = AuthService()
        password = "secure_password_123"
        wrong_password = "wrong_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(wrong_password, hashed) is False


class TestUserModels:
    """Test Pydantic models for authentication."""

    def test_user_background_defaults(self):
        """Test UserBackground has correct defaults."""
        background = UserBackground()

        assert background.software_experience == "beginner"
        assert background.hardware_experience == "beginner"
        assert background.programming_languages == []
        assert background.robotics_experience is False
        assert background.ai_experience is False

    def test_user_background_custom_values(self):
        """Test UserBackground with custom values."""
        background = UserBackground(
            software_experience="advanced",
            hardware_experience="intermediate",
            programming_languages=["Python", "JavaScript"],
            robotics_experience=True,
            ai_experience=True,
        )

        assert background.software_experience == "advanced"
        assert background.hardware_experience == "intermediate"
        assert background.programming_languages == ["Python", "JavaScript"]
        assert background.robotics_experience is True
        assert background.ai_experience is True

    def test_user_create_with_background(self):
        """Test UserCreate model with background."""
        user_data = UserCreate(
            email="test@example.com",
            password="secure_password_123",
            background=UserBackground(
                software_experience="intermediate",
                programming_languages=["Python"],
            ),
        )

        assert user_data.email == "test@example.com"
        assert user_data.password == "secure_password_123"
        assert user_data.background.software_experience == "intermediate"

    def test_user_create_password_min_length(self):
        """Test UserCreate enforces minimum password length."""
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                password="short",  # Less than 8 characters
            )

    def test_user_login_model(self):
        """Test UserLogin model."""
        login_data = UserLogin(
            email="test@example.com",
            password="password123",
        )

        assert login_data.email == "test@example.com"
        assert login_data.password == "password123"


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_register_endpoint_validation_error(self, client):
        """Test registration with invalid data returns 422."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",  # Invalid email format
                "password": "short",  # Too short
            },
        )

        assert response.status_code == 422

    def test_register_endpoint_missing_fields(self, client):
        """Test registration with missing fields returns 422."""
        response = client.post(
            "/api/auth/register",
            json={},
        )

        assert response.status_code == 422

    def test_login_endpoint_validation_error(self, client):
        """Test login with invalid data returns 422."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",
                "password": "password",
            },
        )

        assert response.status_code == 422

    def test_logout_endpoint_missing_token(self, client):
        """Test logout with missing token returns 422."""
        response = client.post(
            "/api/auth/logout",
            json={},
        )

        assert response.status_code == 422

    def test_me_endpoint_no_auth(self, client):
        """Test /me endpoint without authentication returns 401."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_me_endpoint_invalid_token(self, client):
        """Test /me endpoint with invalid token returns 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401
