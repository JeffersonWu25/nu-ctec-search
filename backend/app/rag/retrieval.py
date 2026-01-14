"""
Retrieval functions for RAG.

Computes vector similarity in Python for easy iteration and debugging.
"""

from typing import List, Dict, Any
import numpy as np

from ..db.rag import fetch_chunks_with_embeddings_for_offering
from .embeddings import generate_embeddings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve_similar_chunks(
    query: str,
    course_offering_id: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve the most similar comment chunks for a query within a course offering.

    This is the main entry point for RAG retrieval. It:
    1. Generates an embedding for the query
    2. Fetches all chunks for the offering
    3. Computes cosine similarity in Python
    4. Returns top k chunks with scores and metadata

    Args:
        query: Natural language query (e.g., "Is this course difficult?")
        course_offering_id: UUID of the course offering to search within
        k: Number of chunks to retrieve (default: 5)

    Returns:
        List of dicts, each containing:
            - chunk_id: UUID of the chunk
            - comment_id: UUID of the source comment (for citations)
            - content: The chunk text
            - similarity: Cosine similarity score (0-1, higher is better)
            - metadata: Dict with course_code, instructor_name, etc.
    """
    # Generate embedding for the query
    embeddings = generate_embeddings([query])
    query_embedding = embeddings[0]

    return retrieve_with_embedding(query_embedding, course_offering_id, k)


def retrieve_with_embedding(
    query_embedding: List[float],
    course_offering_id: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve similar chunks using a pre-computed embedding.

    Use this when you already have the query embedding (e.g., from caching).

    Args:
        query_embedding: 1536-dimensional embedding vector
        course_offering_id: UUID of the course offering
        k: Number of chunks to retrieve

    Returns:
        List of dicts with chunk_id, comment_id, content, similarity, metadata
    """
    # Fetch all chunks with embeddings for this offering
    chunks = fetch_chunks_with_embeddings_for_offering(course_offering_id)

    if not chunks:
        return []

    # Compute similarity for each chunk
    scored_chunks = []
    for chunk in chunks:
        similarity = cosine_similarity(query_embedding, chunk['embedding'])
        scored_chunks.append({
            'chunk_id': chunk['id'],
            'comment_id': chunk['comment_id'],
            'content': chunk['content'],
            'similarity': similarity,
            'metadata': chunk['metadata']
        })

    # Sort by similarity descending and return top k
    scored_chunks.sort(key=lambda x: x['similarity'], reverse=True)

    return scored_chunks[:k]
