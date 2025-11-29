"""Chat message model for storing conversation history."""

import uuid

from sqlalchemy import Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    """Chat message model for storing RAG chatbot conversations."""

    __tablename__ = "chat_messages"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    selected_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="chat_messages")
