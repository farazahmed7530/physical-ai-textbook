"""Content models for personalization and translation caching."""

import uuid

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PersonalizedContent(Base, UUIDMixin, TimestampMixin):
    """Cached personalized content for users."""

    __tablename__ = "personalized_content"
    __table_args__ = (
        UniqueConstraint("user_id", "chapter_id", name="uq_personalized_user_chapter"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    chapter_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    personalized_content: Mapped[str] = mapped_column(Text, nullable=False)
    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="personalized_content")


class TranslatedContent(Base, UUIDMixin, TimestampMixin):
    """Cached translated content for chapters."""

    __tablename__ = "translated_content"
    __table_args__ = (
        UniqueConstraint("chapter_id", "language", name="uq_translated_chapter_language"),
    )

    chapter_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    translated_content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="ur", nullable=False)
