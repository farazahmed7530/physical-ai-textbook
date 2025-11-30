"""Content parser and chunker for textbook MDX/Markdown files.

This module provides functionality to:
- Parse markdown/MDX files and extract text content
- Create semantic chunks with configurable size and overlap
- Extract metadata (chapter_id, section_title, page_url)

Requirements: 4.1
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class ContentMetadata:
    """Metadata extracted from a content file."""

    chapter_id: str
    title: str
    section_title: str
    page_url: str
    sidebar_position: int | None = None


@dataclass
class ContentChunk:
    """A chunk of content with metadata."""

    id: str
    content: str
    metadata: ContentMetadata
    position: int  # Position of chunk within the chapter
    token_count: int

    def to_dict(self) -> dict:
        """Convert chunk to dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "chapter_id": self.metadata.chapter_id,
            "title": self.metadata.title,
            "section_title": self.metadata.section_title,
            "page_url": self.metadata.page_url,
            "position": self.position,
            "token_count": self.token_count,
        }


@dataclass
class ParsedContent:
    """Parsed content from a markdown/MDX file."""

    raw_content: str
    text_content: str  # Content with MDX/special elements removed
    metadata: ContentMetadata
    sections: list[tuple[str, str]] = field(default_factory=list)  # (heading, content)


class ContentParser:
    """Parser for markdown/MDX textbook content."""

    # Patterns for MDX/Docusaurus-specific elements to remove or process
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    MDX_IMPORT_PATTERN = re.compile(r"^import\s+.*?$", re.MULTILINE)
    MDX_EXPORT_PATTERN = re.compile(r"^export\s+.*?$", re.MULTILINE)
    JSX_COMPONENT_PATTERN = re.compile(r"<[A-Z][a-zA-Z]*[^>]*>.*?</[A-Z][a-zA-Z]*>", re.DOTALL)
    JSX_SELF_CLOSING_PATTERN = re.compile(r"<[A-Z][a-zA-Z]*[^>]*/\s*>")
    MERMAID_PATTERN = re.compile(r"```mermaid\n.*?```", re.DOTALL)
    CODE_BLOCK_PATTERN = re.compile(r"```[\w]*\n.*?```", re.DOTALL)
    ADMONITION_PATTERN = re.compile(r":::(tip|note|caution|warning|info|danger)\s*(.*?)\n(.*?):::", re.DOTALL)
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
    IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\([^)]+\)")

    def __init__(self, base_url: str = ""):
        """Initialize parser with base URL for generating page URLs."""
        self.base_url = base_url.rstrip("/")

    def parse_file(self, file_path: Path) -> ParsedContent:
        """Parse a markdown/MDX file and extract content with metadata."""
        raw_content = file_path.read_text(encoding="utf-8")
        return self.parse_content(raw_content, file_path)

    def parse_content(self, raw_content: str, file_path: Path) -> ParsedContent:
        """Parse raw markdown/MDX content."""
        # Extract frontmatter metadata
        metadata = self._extract_metadata(raw_content, file_path)

        # Remove frontmatter for text processing
        content_without_frontmatter = self.FRONTMATTER_PATTERN.sub("", raw_content)

        # Extract text content (remove MDX-specific elements)
        text_content = self._extract_text_content(content_without_frontmatter)

        # Extract sections
        sections = self._extract_sections(content_without_frontmatter)

        return ParsedContent(
            raw_content=raw_content,
            text_content=text_content,
            metadata=metadata,
            sections=sections,
        )

    def _extract_metadata(self, content: str, file_path: Path) -> ContentMetadata:
        """Extract metadata from frontmatter and file path."""
        # Default values from file path
        chapter_id = file_path.stem
        title = chapter_id.replace("-", " ").title()
        sidebar_position = None

        # Parse frontmatter if present
        frontmatter_match = self.FRONTMATTER_PATTERN.match(content)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # Extract title
            title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip().strip('"\'')

            # Extract sidebar_position
            position_match = re.search(r"sidebar_position:\s*(\d+)", frontmatter)
            if position_match:
                sidebar_position = int(position_match.group(1))

        # Generate page URL from file path
        page_url = self._generate_page_url(file_path)

        # Determine section title from first heading or title
        section_title = title

        return ContentMetadata(
            chapter_id=chapter_id,
            title=title,
            section_title=section_title,
            page_url=page_url,
            sidebar_position=sidebar_position,
        )

    def _generate_page_url(self, file_path: Path) -> str:
        """Generate page URL from file path."""
        # Convert path like 'docs/introduction/physical-ai.mdx' to '/introduction/physical-ai'
        parts = file_path.parts
        # Find 'docs' in path and take everything after
        try:
            docs_index = parts.index("docs")
            url_parts = parts[docs_index + 1 :]
        except ValueError:
            url_parts = parts

        # Remove file extension and join
        url_path = "/".join(url_parts)
        url_path = re.sub(r"\.(mdx?|md)$", "", url_path)

        return f"{self.base_url}/{url_path}"

    def _extract_text_content(self, content: str) -> str:
        """Extract plain text content, removing MDX-specific elements."""
        text = content

        # Remove MDX imports and exports
        text = self.MDX_IMPORT_PATTERN.sub("", text)
        text = self.MDX_EXPORT_PATTERN.sub("", text)

        # Remove mermaid diagrams (keep a placeholder)
        text = self.MERMAID_PATTERN.sub("[Diagram]", text)

        # Process code blocks - keep the code but mark it
        def process_code_block(match: re.Match) -> str:
            code = match.group(0)
            # Extract language if present
            lang_match = re.match(r"```(\w+)", code)
            lang = lang_match.group(1) if lang_match else "code"
            # Extract code content
            code_content = re.sub(r"```\w*\n?", "", code).strip()
            return f"[Code example in {lang}]: {code_content[:200]}..." if len(code_content) > 200 else f"[Code example in {lang}]: {code_content}"

        text = self.CODE_BLOCK_PATTERN.sub(process_code_block, text)

        # Process admonitions - keep the content
        def process_admonition(match: re.Match) -> str:
            admon_type = match.group(1)
            title = match.group(2).strip() if match.group(2) else admon_type.title()
            content = match.group(3).strip()
            return f"{title}: {content}"

        text = self.ADMONITION_PATTERN.sub(process_admonition, text)

        # Remove JSX components
        text = self.JSX_COMPONENT_PATTERN.sub("", text)
        text = self.JSX_SELF_CLOSING_PATTERN.sub("", text)

        # Convert links to just text
        text = self.LINK_PATTERN.sub(r"\1", text)

        # Remove images but keep alt text
        text = self.IMAGE_PATTERN.sub(r"[Image: \1]", text)

        # Clean up extra whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text

    def _extract_sections(self, content: str) -> list[tuple[str, str]]:
        """Extract sections based on headings."""
        sections = []
        current_heading = "Introduction"
        current_content = []

        lines = content.split("\n")
        for line in lines:
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                # Save previous section if it has content
                if current_content:
                    sections.append((current_heading, "\n".join(current_content).strip()))
                current_heading = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content:
            sections.append((current_heading, "\n".join(current_content).strip()))

        return sections


class ContentChunker:
    """Semantic chunker for textbook content."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        """Initialize chunker with size parameters.

        Args:
            chunk_size: Target chunk size in tokens (approximate).
            chunk_overlap: Number of tokens to overlap between chunks.
            min_chunk_size: Minimum chunk size to avoid tiny chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation).

        Uses a simple heuristic: ~4 characters per token for English text.
        """
        return len(text) // 4

    def chunk_content(self, parsed_content: ParsedContent) -> list[ContentChunk]:
        """Split parsed content into semantic chunks."""
        chunks = []
        position = 0

        # Process each section
        for section_title, section_content in parsed_content.sections:
            # Update metadata with current section
            section_metadata = ContentMetadata(
                chapter_id=parsed_content.metadata.chapter_id,
                title=parsed_content.metadata.title,
                section_title=section_title,
                page_url=parsed_content.metadata.page_url,
                sidebar_position=parsed_content.metadata.sidebar_position,
            )

            # Chunk the section content
            for chunk_text in self._split_text(section_content):
                token_count = self.estimate_tokens(chunk_text)
                if token_count < self.min_chunk_size:
                    continue

                chunk_id = self._generate_chunk_id(
                    parsed_content.metadata.chapter_id,
                    section_title,
                    position,
                )

                chunks.append(
                    ContentChunk(
                        id=chunk_id,
                        content=chunk_text,
                        metadata=section_metadata,
                        position=position,
                        token_count=token_count,
                    )
                )
                position += 1

        return chunks

    def _split_text(self, text: str) -> Iterator[str]:
        """Split text into chunks with overlap."""
        if not text.strip():
            return

        # Split by paragraphs first
        paragraphs = re.split(r"\n\n+", text)
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = self.estimate_tokens(para)

            # If single paragraph exceeds chunk size, split it further
            if para_tokens > self.chunk_size:
                # Yield current chunk if any
                if current_chunk:
                    yield "\n\n".join(current_chunk)
                    current_chunk = []
                    current_size = 0

                # Split large paragraph by sentences
                for sentence_chunk in self._split_large_paragraph(para):
                    yield sentence_chunk
                continue

            # Check if adding this paragraph exceeds chunk size
            if current_size + para_tokens > self.chunk_size and current_chunk:
                yield "\n\n".join(current_chunk)

                # Keep overlap - take last paragraph(s) up to overlap size
                overlap_chunks = []
                overlap_size = 0
                for prev_para in reversed(current_chunk):
                    prev_size = self.estimate_tokens(prev_para)
                    if overlap_size + prev_size <= self.chunk_overlap:
                        overlap_chunks.insert(0, prev_para)
                        overlap_size += prev_size
                    else:
                        break

                current_chunk = overlap_chunks
                current_size = overlap_size

            current_chunk.append(para)
            current_size += para_tokens

        # Yield remaining content
        if current_chunk:
            yield "\n\n".join(current_chunk)

    def _split_large_paragraph(self, paragraph: str) -> Iterator[str]:
        """Split a large paragraph by sentences."""
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_tokens = self.estimate_tokens(sentence)

            if current_size + sentence_tokens > self.chunk_size and current_chunk:
                yield " ".join(current_chunk)
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_tokens

        if current_chunk:
            yield " ".join(current_chunk)

    def _generate_chunk_id(self, chapter_id: str, section_title: str, position: int) -> str:
        """Generate a unique, deterministic chunk ID as a valid UUID.

        Qdrant requires point IDs to be either unsigned integers or valid UUIDs.
        We generate a deterministic UUID v5 based on the content identifiers.
        """
        import uuid
        # Use UUID v5 with a namespace to generate deterministic UUIDs
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
        content = f"{chapter_id}:{section_title}:{position}"
        return str(uuid.uuid5(namespace, content))


def parse_textbook_directory(
    docs_path: Path,
    base_url: str = "",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[ContentChunk]:
    """Parse all markdown/MDX files in a textbook docs directory.

    Args:
        docs_path: Path to the docs directory.
        base_url: Base URL for generating page URLs.
        chunk_size: Target chunk size in tokens.
        chunk_overlap: Token overlap between chunks.

    Returns:
        List of all content chunks from all files.
    """
    parser = ContentParser(base_url=base_url)
    chunker = ContentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    all_chunks = []

    # Find all markdown/MDX files
    for pattern in ["**/*.md", "**/*.mdx"]:
        for file_path in docs_path.glob(pattern):
            # Skip template files
            if "_templates" in str(file_path):
                continue

            try:
                parsed = parser.parse_file(file_path)
                chunks = chunker.chunk_content(parsed)
                all_chunks.extend(chunks)
            except Exception as e:
                # Log error but continue processing other files
                print(f"Error parsing {file_path}: {e}")

    return all_chunks
