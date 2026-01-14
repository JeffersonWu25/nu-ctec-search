"""
Unified retrieval for RAG using rag_chunks + rag_embeddings.

Uses Postgres vector similarity (<=>) via the ivfflat index for efficient
similarity search across both comment and catalog chunks.

This module is designed for the discovery feature, supporting:
- Filtering by entity_type and entity_id
- Optional filtering by chunk_type (comment, catalog_description, catalog_prereqs)
- Efficient indexed vector search

NOTE: Requires the following SQL function to be created in Supabase:

    CREATE OR REPLACE FUNCTION search_rag_chunks(
        query_embedding vector(1536),
        match_entity_type text DEFAULT NULL,
        match_entity_id uuid DEFAULT NULL,
        match_chunk_types text[] DEFAULT NULL,
        match_count int DEFAULT 10
    )
    RETURNS TABLE (
        chunk_id uuid,
        content text,
        metadata jsonb,
        entity_type text,
        entity_id uuid,
        chunk_type text,
        similarity float
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            rc.id AS chunk_id,
            rc.content,
            rc.metadata,
            rc.entity_type,
            rc.entity_id,
            rc.chunk_type,
            1 - (re.embedding <=> query_embedding) AS similarity
        FROM rag_chunks rc
        JOIN rag_embeddings re ON re.chunk_id = rc.id
        WHERE
            (match_entity_type IS NULL OR rc.entity_type = match_entity_type)
            AND (match_entity_id IS NULL OR rc.entity_id = match_entity_id)
            AND (match_chunk_types IS NULL OR rc.chunk_type = ANY(match_chunk_types))
        ORDER BY re.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$;

"""

from typing import List, Dict, Any, Optional
from ..supabase_client import supabase
from .embeddings import generate_embeddings


def retrieve_rag_chunks(
    query_embedding: List[float],
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    k: int = 8,
    chunk_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k similar chunks from rag_chunks using Postgres vector search.

    Uses the indexed <=> operator for efficient cosine distance search.

    Args:
        query_embedding: 1536-dimensional query embedding vector
        entity_type: Filter by entity type ('course_offering' or 'course').
                    None means search across all entity types.
        entity_id: Filter by specific entity ID. None means search all entities.
        k: Number of top results to return (default: 8)
        chunk_types: Optional list of chunk_types to filter by
                    (e.g., ['comment'], ['catalog_description', 'catalog_prereqs']).
                    None means include all chunk types.

    Returns:
        List of dicts, each containing:
            - chunk_id: UUID of the chunk
            - content: The chunk text
            - similarity: Cosine similarity score (0-1, higher is better)
            - metadata: Dict with course_code, instructor_name, etc.
            - entity_type: 'course_offering' or 'course'
            - entity_id: UUID of the entity
            - chunk_type: 'comment', 'catalog_description', or 'catalog_prereqs'
    """
    response = supabase.rpc(
        'search_rag_chunks',
        {
            'query_embedding': query_embedding,
            'match_entity_type': entity_type,
            'match_entity_id': entity_id,
            'match_chunk_types': chunk_types,
            'match_count': k
        }
    ).execute()

    results = []
    for row in response.data or []:
        results.append({
            'chunk_id': row['chunk_id'],
            'content': row['content'],
            'similarity': row['similarity'],
            'metadata': row['metadata'],
            'entity_type': row['entity_type'],
            'entity_id': row['entity_id'],
            'chunk_type': row['chunk_type']
        })

    return results


def retrieve_similar_chunks_unified(
    query: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    k: int = 8,
    chunk_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve similar chunks for a text query (convenience wrapper).

    Generates the embedding for the query and calls retrieve_rag_chunks.

    Args:
        query: Natural language query string
        entity_type: Optional filter by entity type
        entity_id: Optional filter by entity ID
        k: Number of results to return
        chunk_types: Optional filter by chunk types

    Returns:
        List of chunk dicts with similarity scores
    """
    embeddings = generate_embeddings([query])
    query_embedding = embeddings[0]

    return retrieve_rag_chunks(
        query_embedding=query_embedding,
        entity_type=entity_type,
        entity_id=entity_id,
        k=k,
        chunk_types=chunk_types
    )


def retrieve_comments_for_offering(
    query_embedding: List[float],
    course_offering_id: str,
    k: int = 8
) -> List[Dict[str, Any]]:
    """
    Retrieve comment chunks for a specific course offering.

    Convenience function for offering-specific comment retrieval.

    Args:
        query_embedding: 1536-dimensional query embedding
        course_offering_id: UUID of the course offering
        k: Number of results to return

    Returns:
        List of comment chunks with similarity scores
    """
    return retrieve_rag_chunks(
        query_embedding=query_embedding,
        entity_type='course_offering',
        entity_id=course_offering_id,
        k=k,
        chunk_types=['comment']
    )


def retrieve_catalog_for_course(
    query_embedding: List[float],
    course_id: str,
    k: int = 8,
    include_prereqs: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieve catalog chunks for a specific course.

    Args:
        query_embedding: 1536-dimensional query embedding
        course_id: UUID of the course
        k: Number of results to return
        include_prereqs: Whether to include prerequisites chunks

    Returns:
        List of catalog chunks with similarity scores
    """
    chunk_types = ['catalog_description']
    if include_prereqs:
        chunk_types.append('catalog_prereqs')

    return retrieve_rag_chunks(
        query_embedding=query_embedding,
        entity_type='course',
        entity_id=course_id,
        k=k,
        chunk_types=chunk_types
    )


def discover_courses(
    query_embedding: List[float],
    k: int = 10,
    include_comments: bool = True,
    include_catalog: bool = True
) -> List[Dict[str, Any]]:
    """
    Discover courses across all chunks (for discovery feature).

    Searches across both comments and catalog descriptions without
    filtering by specific entity.

    Args:
        query_embedding: 1536-dimensional query embedding
        k: Number of results to return
        include_comments: Include comment chunks in search
        include_catalog: Include catalog chunks in search

    Returns:
        List of chunks with similarity scores, sorted by relevance
    """
    chunk_types = []
    if include_comments:
        chunk_types.append('comment')
    if include_catalog:
        chunk_types.extend(['catalog_description', 'catalog_prereqs'])

    if not chunk_types:
        return []

    return retrieve_rag_chunks(
        query_embedding=query_embedding,
        entity_type=None,  # Search across all entities
        entity_id=None,
        k=k,
        chunk_types=chunk_types if chunk_types else None
    )
