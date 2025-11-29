"""Tests for chat history storage functionality.

Requirements: 5.1
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers.chat import store_chat_message, ChatRequest, ChatResponse


class TestChatHistoryStorage:
    """Tests for chat history storage."""

    @pytest.mark.asyncio
    async def test_store_chat_message_success(self):
        """Test storing chat message with valid data."""
        # Create mock session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        # Test data
        query = "What is Physical AI?"
        response = "Physical AI refers to AI systems that interact with the physical world."
        sources = [{"chapter_id": "intro", "section_title": "Introduction"}]
        selected_text = "Some selected text"
        user_id = str(uuid.uuid4())

        # Call the function
        await store_chat_message(
            session=mock_session,
            query=query,
            response=response,
            sources=sources,
            selected_text=selected_text,
            user_id=user_id,
        )

        # Verify session.add was called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify the ChatMessage was created with correct data
        added_message = mock_session.add.call_args[0][0]
        assert added_message.query == query
        assert added_message.response == response
        assert added_message.sources == sources
        assert added_message.selected_text == selected_text
        assert added_message.user_id == uuid.UUID(user_id)

    @pytest.mark.asyncio
    async def test_store_chat_message_without_user_id(self):
        """Test storing chat message without user_id (anonymous user)."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        await store_chat_message(
            session=mock_session,
            query="Test query",
            response="Test response",
            sources=[],
            selected_text=None,
            user_id=None,
        )

        mock_session.add.assert_called_once()
        added_message = mock_session.add.call_args[0][0]
        assert added_message.user_id is None

    @pytest.mark.asyncio
    async def test_store_chat_message_no_session(self):
        """Test that storage is skipped when session is None."""
        # Should not raise any errors
        await store_chat_message(
            session=None,
            query="Test query",
            response="Test response",
            sources=[],
            selected_text=None,
            user_id=None,
        )
        # No assertions needed - just verify no exception is raised

    @pytest.mark.asyncio
    async def test_store_chat_message_handles_db_error(self):
        """Test that database errors are handled gracefully."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_session.rollback = AsyncMock()

        # Should not raise - errors are logged but not propagated
        await store_chat_message(
            session=mock_session,
            query="Test query",
            response="Test response",
            sources=[],
            selected_text=None,
            user_id=None,
        )

        # Verify rollback was called
        mock_session.rollback.assert_called_once()


class TestChatRequestValidation:
    """Tests for ChatRequest validation."""

    def test_valid_request(self):
        """Test valid chat request."""
        request = ChatRequest(
            query="What is Physical AI?",
            selected_text="Some context",
            user_id=str(uuid.uuid4()),
        )
        assert request.query == "What is Physical AI?"
        assert request.selected_text == "Some context"

    def test_query_stripped(self):
        """Test that query is stripped of whitespace."""
        request = ChatRequest(query="  What is Physical AI?  ")
        assert request.query == "What is Physical AI?"

    def test_empty_query_rejected(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            ChatRequest(query="   ")

    def test_selected_text_stripped(self):
        """Test that selected_text is stripped."""
        request = ChatRequest(query="Test", selected_text="  Some text  ")
        assert request.selected_text == "Some text"

    def test_empty_selected_text_becomes_none(self):
        """Test that empty selected_text becomes None."""
        request = ChatRequest(query="Test", selected_text="   ")
        assert request.selected_text is None

    def test_invalid_user_id_rejected(self):
        """Test that invalid user_id is rejected."""
        with pytest.raises(ValueError, match="user_id must be a valid UUID"):
            ChatRequest(query="Test", user_id="not-a-uuid")

    def test_valid_user_id_accepted(self):
        """Test that valid user_id is accepted."""
        valid_uuid = str(uuid.uuid4())
        request = ChatRequest(query="Test", user_id=valid_uuid)
        assert request.user_id == valid_uuid
