"""Authentication service for user registration, login, and session management.

Implements JWT-based authentication with secure password hashing.
Requirements: 6.2, 6.3
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.db.postgres import get_postgres_db

logger = logging.getLogger(__name__)


class UserBackground(BaseModel):
    """User background information for personalization."""
    software_experience: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    hardware_experience: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    programming_languages: list[str] = Field(default_factory=list)
    robotics_experience: bool = False
    ai_experience: bool = False


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    background: UserBackground = Field(default_factory=UserBackground)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: str
    email: str
    software_experience: Optional[str] = None
    hardware_experience: Optional[str] = None
    programming_languages: Optional[list[str]] = None
    robotics_experience: bool = False
    ai_experience: bool = False
    created_at: datetime


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthResponse(BaseModel):
    """Schema for authentication response with user and token."""
    user: UserResponse
    token: TokenResponse


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self):
        """Initialize auth service with settings."""
        self.settings = get_settings()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
        """Create a JWT access token.

        Returns:
            Tuple of (token, expiration_datetime)
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_expire_minutes)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),  # Unique token ID
        }

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )

        return encoded_jwt, expire

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token.

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token decode failed: {e}")
            return None

    async def register_user(self, user_data: UserCreate) -> Optional[AuthResponse]:
        """Register a new user with background information.

        Requirements: 6.1, 6.5
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.error("Database pool not available")
            return None

        # Hash the password
        password_hash = self.hash_password(user_data.password)
        user_id = str(uuid.uuid4())

        try:
            async with pool.acquire() as conn:
                # Check if user already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1",
                    user_data.email
                )

                if existing:
                    logger.warning(f"Registration attempt for existing email: {user_data.email}")
                    return None

                # Insert new user
                await conn.execute(
                    """
                    INSERT INTO users (
                        id, email, password_hash, software_experience, hardware_experience,
                        programming_languages, robotics_experience, ai_experience
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    uuid.UUID(user_id),
                    user_data.email,
                    password_hash,
                    user_data.background.software_experience,
                    user_data.background.hardware_experience,
                    user_data.background.programming_languages,
                    user_data.background.robotics_experience,
                    user_data.background.ai_experience,
                )

                # Fetch the created user
                user_row = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1",
                    uuid.UUID(user_id)
                )

                if not user_row:
                    return None

                # Create session token
                token, expires_at = self.create_access_token(user_id)

                # Store session in database
                session_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO sessions (id, user_id, token, expires_at)
                    VALUES ($1, $2, $3, $4)
                    """,
                    uuid.UUID(session_id),
                    uuid.UUID(user_id),
                    token,
                    expires_at,
                )

                user_response = UserResponse(
                    id=str(user_row["id"]),
                    email=user_row["email"],
                    software_experience=user_row["software_experience"],
                    hardware_experience=user_row["hardware_experience"],
                    programming_languages=user_row["programming_languages"],
                    robotics_experience=user_row["robotics_experience"],
                    ai_experience=user_row["ai_experience"],
                    created_at=user_row["created_at"],
                )

                token_response = TokenResponse(
                    access_token=token,
                    expires_at=expires_at,
                )

                logger.info(f"User registered successfully: {user_data.email}")
                return AuthResponse(user=user_response, token=token_response)

        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return None


    async def login_user(self, credentials: UserLogin) -> Optional[AuthResponse]:
        """Authenticate user and create session.

        Requirements: 6.2, 6.4
        Returns None for any authentication failure (security: don't reveal failure reason)
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.error("Database pool not available")
            return None

        try:
            async with pool.acquire() as conn:
                # Fetch user by email
                user_row = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1",
                    credentials.email
                )

                # Security: Don't reveal if email exists or password is wrong
                if not user_row:
                    logger.warning(f"Login attempt for non-existent email")
                    return None

                # Verify password
                if not self.verify_password(credentials.password, user_row["password_hash"]):
                    logger.warning(f"Invalid password attempt for user: {credentials.email}")
                    return None

                user_id = str(user_row["id"])

                # Create new session token
                token, expires_at = self.create_access_token(user_id)

                # Store session in database
                session_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO sessions (id, user_id, token, expires_at)
                    VALUES ($1, $2, $3, $4)
                    """,
                    uuid.UUID(session_id),
                    uuid.UUID(user_id),
                    token,
                    expires_at,
                )

                user_response = UserResponse(
                    id=user_id,
                    email=user_row["email"],
                    software_experience=user_row["software_experience"],
                    hardware_experience=user_row["hardware_experience"],
                    programming_languages=user_row["programming_languages"],
                    robotics_experience=user_row["robotics_experience"],
                    ai_experience=user_row["ai_experience"],
                    created_at=user_row["created_at"],
                )

                token_response = TokenResponse(
                    access_token=token,
                    expires_at=expires_at,
                )

                logger.info(f"User logged in successfully: {credentials.email}")
                return AuthResponse(user=user_response, token=token_response)

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return None

    async def logout_user(self, token: str) -> bool:
        """Invalidate a session token.

        Requirements: 6.3
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            logger.error("Database pool not available")
            return False

        try:
            async with pool.acquire() as conn:
                # Delete the session
                result = await conn.execute(
                    "DELETE FROM sessions WHERE token = $1",
                    token
                )

                # Check if a session was actually deleted
                deleted = result.split()[-1]
                if deleted == "0":
                    logger.warning("Logout attempt with invalid token")
                    return False

                logger.info("User logged out successfully")
                return True

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    async def validate_session(self, token: str) -> Optional[UserResponse]:
        """Validate a session token and return user if valid.

        Requirements: 6.2
        """
        # First decode the JWT
        payload = self.decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        db = get_postgres_db()
        pool = db.pool

        if not pool:
            return None

        try:
            async with pool.acquire() as conn:
                # Check if session exists and is not expired
                session = await conn.fetchrow(
                    """
                    SELECT s.*, u.* FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.token = $1 AND s.expires_at > NOW()
                    """,
                    token
                )

                if not session:
                    return None

                return UserResponse(
                    id=str(session["user_id"]),
                    email=session["email"],
                    software_experience=session["software_experience"],
                    hardware_experience=session["hardware_experience"],
                    programming_languages=session["programming_languages"],
                    robotics_experience=session["robotics_experience"],
                    ai_experience=session["ai_experience"],
                    created_at=session["created_at"],
                )

        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from the database.

        Returns the number of sessions removed.
        """
        db = get_postgres_db()
        pool = db.pool

        if not pool:
            return 0

        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE expires_at < NOW()"
                )
                deleted = int(result.split()[-1])
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} expired sessions")
                return deleted

        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            return 0


# Global auth service instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the global auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
