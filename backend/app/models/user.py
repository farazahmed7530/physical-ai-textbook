"""User model for authentication and personalization."""

from datetime import datetime
import uuid

from sqlalchemy import Boolean, String, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication and storing background preferences."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Background information for personalization
    software_experience: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hardware_experience: Mapped[str | None] = mapped_column(String(20), nullable=True)
    programming_languages: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    robotics_experience: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_experience: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="user", cascade="all, delete-orphan"
    )
    personalized_content: Mapped[list["PersonalizedContent"]] = relationship(
        "PersonalizedContent", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base, UUIDMixin):
    """Session model for Better-Auth token management."""

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
