#!/usr/bin/env python3
"""CLI script to index textbook content into Qdrant.

This script parses the textbook docs directory, generates embeddings,
and indexes the content into Qdrant for RAG retrieval.

Usage:
    python scripts/index_content.py --docs-path ../textbook/docs --base-url https://example.com
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.db.qdrant import init_qdrant, close_qdrant
from app.services.indexer_service import index_textbook_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main(docs_path: Path, base_url: str) -> int:
    """Main indexing function.

    Args:
        docs_path: Path to the docs directory.
        base_url: Base URL for generating page URLs.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    settings = get_settings()

    # Validate configuration
    if not settings.has_qdrant_config:
        logger.error("Qdrant configuration not found. Set QDRANT_URL environment variable.")
        return 1

    if not docs_path.exists():
        logger.error(f"Docs path does not exist: {docs_path}")
        return 1

    try:
        # Initialize Qdrant connection
        logger.info("Connecting to Qdrant...")
        await init_qdrant()

        # Run indexing
        logger.info(f"Indexing content from: {docs_path}")
        result = await index_textbook_content(
            docs_path=docs_path,
            base_url=base_url,
        )

        # Report results
        logger.info("=" * 50)
        logger.info("Indexing Complete!")
        logger.info(f"  Total chunks: {result.total_chunks}")
        logger.info(f"  Indexed: {result.indexed_chunks}")
        logger.info(f"  Failed: {result.failed_chunks}")
        logger.info(f"  Chapters: {', '.join(result.chapters_processed)}")

        if result.errors:
            logger.warning("Errors encountered:")
            for error in result.errors:
                logger.warning(f"  - {error}")

        return 0 if result.failed_chunks == 0 else 1

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        return 1

    finally:
        # Clean up
        await close_qdrant()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Index textbook content into Qdrant vector database."
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        default=Path(__file__).parent.parent.parent / "textbook" / "docs",
        help="Path to the textbook docs directory",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="",
        help="Base URL for generating page URLs",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(main(args.docs_path, args.base_url))
    sys.exit(exit_code)
