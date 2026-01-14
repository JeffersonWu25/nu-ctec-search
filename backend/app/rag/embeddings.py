"""
Embedding generation for RAG.

Uses OpenAI's text-embedding-3-small model (1536 dimensions).
"""

from typing import List
from ..core.openai_client import get_openai_client

# Model produces 1536-dimensional vectors, matching the pgvector column
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (1536 dimensions each)

    Raises:
        OpenAI API errors on failure
    """
    if not texts:
        return []

    client = get_openai_client()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    # Return embeddings in same order as input
    return [item.embedding for item in response.data]
