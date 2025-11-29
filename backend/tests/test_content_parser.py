"""Tests for content parser and chunker."""

import pytest
from pathlib import Path

from app.services.content_parser import (
    ContentParser,
    ContentChunker,
    ContentMetadata,
    ParsedContent,
    ContentChunk,
)


class TestContentParser:
    """Tests for ContentParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return ContentParser(base_url="https://example.com")

    def test_parse_simple_markdown(self, parser):
        """Test parsing simple markdown content."""
        content = """---
sidebar_position: 1
title: "Test Chapter"
---

# Test Chapter

This is a test paragraph.

## Section One

Content for section one.
"""
        file_path = Path("docs/test/chapter.mdx")
        result = parser.parse_content(content, file_path)

        assert isinstance(result, ParsedContent)
        assert result.metadata.title == "Test Chapter"
        assert result.metadata.sidebar_position == 1
        assert "test paragraph" in result.text_content.lower()

    def test_extract_metadata_from_frontmatter(self, parser):
        """Test metadata extraction from frontmatter."""
        content = """---
sidebar_position: 5
title: "My Title"
---

# Content
"""
        file_path = Path("docs/intro/my-chapter.mdx")
        result = parser.parse_content(content, file_path)

        assert result.metadata.title == "My Title"
        assert result.metadata.sidebar_position == 5
        assert result.metadata.chapter_id == "my-chapter"

    def test_extract_metadata_without_frontmatter(self, parser):
        """Test metadata extraction when no frontmatter present."""
        content = "# Simple Content\n\nJust some text."
        file_path = Path("docs/simple-doc.md")
        result = parser.parse_content(content, file_path)

        assert result.metadata.chapter_id == "simple-doc"
        assert result.metadata.title == "Simple Doc"

    def test_generate_page_url(self, parser):
        """Test page URL generation from file path."""
        content = "# Test"
        file_path = Path("docs/introduction/physical-ai.mdx")
        result = parser.parse_content(content, file_path)

        assert result.metadata.page_url == "https://example.com/introduction/physical-ai"

    def test_remove_mermaid_diagrams(self, parser):
        """Test that mermaid diagrams are replaced with placeholder."""
        content = """# Test

```mermaid
graph LR
    A --> B
```

More content.
"""
        file_path = Path("docs/test.md")
        result = parser.parse_content(content, file_path)

        assert "```mermaid" not in result.text_content
        assert "[Diagram]" in result.text_content

    def test_process_code_blocks(self, parser):
        """Test that code blocks are processed correctly."""
        content = """# Test

```python
def hello():
    print("Hello")
```
"""
        file_path = Path("docs/test.md")
        result = parser.parse_content(content, file_path)

        assert "[Code example in python]" in result.text_content

    def test_process_admonitions(self, parser):
        """Test that admonitions are processed correctly."""
        content = """# Test

:::tip Important
This is a tip.
:::
"""
        file_path = Path("docs/test.md")
        result = parser.parse_content(content, file_path)

        assert "Important" in result.text_content or "tip" in result.text_content.lower()

    def test_extract_sections(self, parser):
        """Test section extraction from content."""
        content = """# Main Title

Intro paragraph.

## Section One

Section one content.

## Section Two

Section two content.
"""
        file_path = Path("docs/test.md")
        result = parser.parse_content(content, file_path)

        assert len(result.sections) >= 2
        section_titles = [s[0] for s in result.sections]
        assert "Section One" in section_titles or "Main Title" in section_titles


class TestContentChunker:
    """Tests for ContentChunker class."""

    @pytest.fixture
    def chunker(self):
        """Create chunker instance."""
        return ContentChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)

    @pytest.fixture
    def sample_parsed_content(self):
        """Create sample parsed content."""
        return ParsedContent(
            raw_content="# Test\n\nContent here.",
            text_content="Test content here.",
            metadata=ContentMetadata(
                chapter_id="test-chapter",
                title="Test Chapter",
                section_title="Test",
                page_url="/test-chapter",
                sidebar_position=1,
            ),
            sections=[
                ("Introduction", "This is the introduction paragraph with some content."),
                ("Main Section", "This is the main section with more detailed content that spans multiple sentences. It contains important information."),
            ],
        )

    def test_estimate_tokens(self, chunker):
        """Test token estimation."""
        text = "This is a test sentence with some words."
        tokens = chunker.estimate_tokens(text)
        # Rough estimate: ~4 chars per token
        assert tokens > 0
        assert tokens < len(text)

    def test_chunk_content_creates_chunks(self, chunker, sample_parsed_content):
        """Test that chunking creates content chunks."""
        chunks = chunker.chunk_content(sample_parsed_content)

        assert len(chunks) > 0
        assert all(isinstance(c, ContentChunk) for c in chunks)

    def test_chunk_has_required_fields(self, chunker, sample_parsed_content):
        """Test that chunks have all required fields."""
        chunks = chunker.chunk_content(sample_parsed_content)

        for chunk in chunks:
            assert chunk.id is not None
            assert chunk.content is not None
            assert chunk.metadata is not None
            assert chunk.position >= 0
            assert chunk.token_count > 0

    def test_chunk_metadata_preserved(self, chunker, sample_parsed_content):
        """Test that metadata is preserved in chunks."""
        chunks = chunker.chunk_content(sample_parsed_content)

        for chunk in chunks:
            assert chunk.metadata.chapter_id == "test-chapter"
            assert chunk.metadata.page_url == "/test-chapter"

    def test_chunk_id_is_deterministic(self, chunker, sample_parsed_content):
        """Test that chunk IDs are deterministic."""
        chunks1 = chunker.chunk_content(sample_parsed_content)
        chunks2 = chunker.chunk_content(sample_parsed_content)

        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2):
            assert c1.id == c2.id

    def test_chunk_to_dict(self, chunker, sample_parsed_content):
        """Test chunk serialization to dictionary."""
        chunks = chunker.chunk_content(sample_parsed_content)

        if chunks:
            chunk_dict = chunks[0].to_dict()
            assert "id" in chunk_dict
            assert "content" in chunk_dict
            assert "chapter_id" in chunk_dict
            assert "title" in chunk_dict
            assert "section_title" in chunk_dict
            assert "page_url" in chunk_dict
            assert "position" in chunk_dict
            assert "token_count" in chunk_dict

    def test_empty_content_returns_no_chunks(self, chunker):
        """Test that empty content returns no chunks."""
        parsed = ParsedContent(
            raw_content="",
            text_content="",
            metadata=ContentMetadata(
                chapter_id="empty",
                title="Empty",
                section_title="Empty",
                page_url="/empty",
            ),
            sections=[],
        )
        chunks = chunker.chunk_content(parsed)
        assert len(chunks) == 0

    def test_large_content_creates_multiple_chunks(self):
        """Test that large content is split into multiple chunks."""
        chunker = ContentChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=10)

        # Create content that should result in multiple chunks
        large_section = " ".join(["This is a sentence with some words."] * 20)

        parsed = ParsedContent(
            raw_content=large_section,
            text_content=large_section,
            metadata=ContentMetadata(
                chapter_id="large",
                title="Large",
                section_title="Large",
                page_url="/large",
            ),
            sections=[("Content", large_section)],
        )

        chunks = chunker.chunk_content(parsed)
        assert len(chunks) > 1
