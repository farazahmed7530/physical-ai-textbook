#!/usr/bin/env python3
"""
Script to delete and recreate the Qdrant collection with correct dimensions.

This script will:
1. Delete the existing collection (if it exists)
2. Create a new collection with 768 dimensions (for Gemini embeddings)

Usage:
    cd backend
    python scripts/recreate_qdrant_collection.py

After running this script, you need to re-index your content:
    python scripts/index_content.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load environment variables
load_dotenv(backend_dir / ".env")


def main():
    # Get configuration from environment
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "textbook_content")
    vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "768"))

    if not qdrant_url:
        print("ERROR: QDRANT_URL not set in environment")
        sys.exit(1)

    if not qdrant_api_key:
        print("ERROR: QDRANT_API_KEY not set in environment")
        sys.exit(1)

    print(f"Connecting to Qdrant at: {qdrant_url}")
    print(f"Collection name: {collection_name}")
    print(f"Vector size: {vector_size}")
    print()

    # Create Qdrant client
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name in collection_names:
        print(f"Found existing collection '{collection_name}'")

        # Get collection info
        collection_info = client.get_collection(collection_name)
        old_vector_size = collection_info.config.params.vectors.size
        print(f"Current vector size: {old_vector_size}")

        # Confirm deletion
        response = input(f"\nDelete collection '{collection_name}'? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

        # Delete the collection
        print(f"Deleting collection '{collection_name}'...")
        client.delete_collection(collection_name)
        print("Collection deleted successfully!")
    else:
        print(f"Collection '{collection_name}' does not exist")

    # Create new collection
    print(f"\nCreating new collection '{collection_name}' with {vector_size} dimensions...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )
    print("Collection created successfully!")

    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"\nNew collection info:")
    print(f"  - Name: {collection_name}")
    print(f"  - Vector size: {collection_info.config.params.vectors.size}")
    print(f"  - Distance: {collection_info.config.params.vectors.distance}")
    print(f"  - Points count: {collection_info.points_count}")

    print("\n" + "=" * 50)
    print("SUCCESS! Collection recreated with correct dimensions.")
    print("\nNext step: Re-index your content by running:")
    print("  python scripts/index_content.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
