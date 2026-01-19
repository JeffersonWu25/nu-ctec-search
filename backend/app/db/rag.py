"""
RAG (Retrieval Augmented Generation) database operations.

Handles CRUD operations for rag_chunks and rag_embeddings tables.
"""

from typing import Dict, List, Optional, Set
from ..supabase_client import supabase
from ..utils.logging import get_job_logger


def get_existing_comment_chunk_ids() -> Set[str]:
    """
    Get all comment IDs that already have RAG chunks.

    Uses pagination to fetch beyond Supabase's default 1000 row limit.

    Returns:
        Set of comment IDs (entity_id) that exist in rag_chunks
    """
    logger = get_job_logger('rag')

    PAGE_SIZE = 1000
    all_ids: Set[str] = set()
    offset = 0

    try:
        while True:
            response = supabase.table('rag_chunks') \
                .select('entity_id') \
                .eq('entity_type', 'comment') \
                .eq('chunk_type', 'student_comment') \
                .range(offset, offset + PAGE_SIZE - 1) \
                .execute()

            if not response.data:
                break

            for row in response.data:
                all_ids.add(row['entity_id'])

            if len(response.data) < PAGE_SIZE:
                break

            offset += PAGE_SIZE

        return all_ids
    except Exception as e:
        logger.error("Failed to get existing comment chunk IDs: %s", e)
        return set()


def get_comments_with_offering_data(
    limit: Optional[int] = None,
    exclude_ids: Optional[Set[str]] = None
) -> List[Dict]:
    """
    Get all comments with their course_offering metadata.

    Uses pagination to fetch beyond Supabase's default 1000 row limit.

    Args:
        limit: Maximum number of comments to return
        exclude_ids: Set of comment IDs to exclude (already processed)

    Returns:
        List of comment dicts with course_offering, course_id, instructor_id
    """
    logger = get_job_logger('rag')

    PAGE_SIZE = 1000
    results = []
    offset = 0

    try:
        while True:
            query = supabase.table('comments') \
                .select('''
                    id,
                    content,
                    course_offering_id,
                    course_offerings!inner(
                        course_id,
                        instructor_id
                    )
                ''') \
                .range(offset, offset + PAGE_SIZE - 1)

            response = query.execute()

            if not response.data:
                break

            for row in response.data:
                # Skip if in exclude list
                if exclude_ids and row['id'] in exclude_ids:
                    continue

                # Extract nested course_offering data
                offering = row.get('course_offerings', {})

                results.append({
                    'id': row['id'],
                    'content': row['content'],
                    'course_offering_id': row['course_offering_id'],
                    'course_id': offering.get('course_id'),
                    'instructor_id': offering.get('instructor_id')
                })

                # Check if we've hit the user-specified limit
                if limit and len(results) >= limit:
                    logger.info("Retrieved %d comments for processing (limit reached)", len(results))
                    return results[:limit]

            # If we got fewer rows than PAGE_SIZE, we've reached the end
            if len(response.data) < PAGE_SIZE:
                break

            offset += PAGE_SIZE
            logger.info("Fetched %d comments so far, continuing pagination...", len(results))

        logger.info("Retrieved %d comments for processing", len(results))
        return results

    except Exception as e:
        logger.error("Failed to get comments with offering data: %s", e)
        return []


def insert_rag_chunk(
    entity_type: str,
    entity_id: str,
    content: str,
    chunk_type: str,
    course_id: Optional[str] = None,
    instructor_id: Optional[str] = None,
    course_offering_id: Optional[str] = None,
    chunk_index: int = 0,
    metadata: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Insert a RAG chunk record.

    Args:
        entity_type: Type of entity ('comment', 'course_description', etc.)
        entity_id: UUID of the source entity
        content: The text content of the chunk
        chunk_type: Type of chunk ('student_comment', 'description', etc.)
        course_id: Associated course UUID
        instructor_id: Associated instructor UUID
        course_offering_id: Associated course_offering UUID
        chunk_index: Index for multi-chunk entities (default 0)
        metadata: Optional JSON metadata

    Returns:
        Inserted record dict or None on failure
    """
    logger = get_job_logger('rag')

    try:
        data = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'content': content,
            'chunk_type': chunk_type,
            'chunk_index': chunk_index,
            'metadata': metadata or {}
        }

        if course_id:
            data['course_id'] = course_id
        if instructor_id:
            data['instructor_id'] = instructor_id
        if course_offering_id:
            data['course_offering_id'] = course_offering_id

        response = supabase.table('rag_chunks').insert(data).execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        logger.error("Failed to insert RAG chunk for %s %s: %s", entity_type, entity_id, e)
        return None


def insert_rag_embedding(
    chunk_id: str,
    embedding: List[float],
    model: str
) -> Optional[Dict]:
    """
    Insert a RAG embedding record.

    Args:
        chunk_id: UUID of the rag_chunk
        embedding: Vector embedding (1536 dimensions for text-embedding-3-small)
        model: Model used for embedding

    Returns:
        Inserted record dict or None on failure
    """
    logger = get_job_logger('rag')

    try:
        data = {
            'chunk_id': chunk_id,
            'embedding': embedding,
            'model': model
        }

        response = supabase.table('rag_embeddings').insert(data).execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        logger.error("Failed to insert RAG embedding for chunk %s: %s", chunk_id, e)
        return None


def batch_insert_rag_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Batch insert multiple RAG chunks.

    Args:
        chunks: List of chunk dicts with required fields

    Returns:
        List of inserted records
    """
    logger = get_job_logger('rag')

    if not chunks:
        return []

    try:
        response = supabase.table('rag_chunks').insert(chunks).execute()
        logger.info("Batch inserted %d RAG chunks", len(response.data))
        return response.data

    except Exception as e:
        logger.error("Failed to batch insert RAG chunks: %s", e)
        return []


def batch_insert_rag_embeddings(embeddings: List[Dict]) -> List[Dict]:
    """
    Batch insert multiple RAG embeddings.

    Args:
        embeddings: List of embedding dicts with chunk_id, embedding, model

    Returns:
        List of inserted records
    """
    logger = get_job_logger('rag')

    if not embeddings:
        return []

    try:
        response = supabase.table('rag_embeddings').insert(embeddings).execute()
        logger.info("Batch inserted %d RAG embeddings", len(response.data))
        return response.data

    except Exception as e:
        logger.error("Failed to batch insert RAG embeddings: %s", e)
        return []


def get_chunks_without_embeddings() -> List[Dict]:
    """
    Get chunks that don't have embeddings yet, with full content.

    Uses pagination to handle large datasets.

    Returns:
        List of chunk dicts with id, entity_id, content, entity_type
    """
    logger = get_job_logger('rag')

    PAGE_SIZE = 1000

    try:
        # Step 1: Get all embedded chunk IDs (with pagination)
        embedded_chunk_ids: Set[str] = set()
        offset = 0

        while True:
            embeddings_response = supabase.table('rag_embeddings') \
                .select('chunk_id') \
                .range(offset, offset + PAGE_SIZE - 1) \
                .execute()

            if not embeddings_response.data:
                break

            for row in embeddings_response.data:
                embedded_chunk_ids.add(row['chunk_id'])

            if len(embeddings_response.data) < PAGE_SIZE:
                break

            offset += PAGE_SIZE

        # Step 2: Get all chunks and filter out those with embeddings (with pagination)
        chunks_without_embeddings: List[Dict] = []
        offset = 0

        while True:
            chunks_response = supabase.table('rag_chunks') \
                .select('id, entity_id, content, entity_type, course_offering_id') \
                .range(offset, offset + PAGE_SIZE - 1) \
                .execute()

            if not chunks_response.data:
                break

            for chunk in chunks_response.data:
                if chunk['id'] not in embedded_chunk_ids:
                    chunks_without_embeddings.append(chunk)

            if len(chunks_response.data) < PAGE_SIZE:
                break

            offset += PAGE_SIZE

        logger.info("Found %d chunks without embeddings", len(chunks_without_embeddings))
        return chunks_without_embeddings

    except Exception as e:
        logger.error("Failed to get chunks without embeddings: %s", e)
        return []


def delete_chunk(chunk_id: str) -> bool:
    """
    Delete a RAG chunk (and its embedding via CASCADE).

    Args:
        chunk_id: UUID of the chunk to delete

    Returns:
        True if successful, False otherwise
    """
    logger = get_job_logger('rag')

    try:
        supabase.table('rag_chunks') \
            .delete() \
            .eq('id', chunk_id) \
            .execute()
        return True
    except Exception as e:
        logger.error("Failed to delete chunk %s: %s", chunk_id, e)
        return False


def get_rag_stats() -> Dict:
    """
    Get statistics about RAG tables.

    Returns:
        Dict with counts and stats
    """
    logger = get_job_logger('rag')

    try:
        chunks_response = supabase.table('rag_chunks') \
            .select('id', count='exact') \
            .execute()

        embeddings_response = supabase.table('rag_embeddings') \
            .select('chunk_id', count='exact') \
            .execute()

        comment_chunks_response = supabase.table('rag_chunks') \
            .select('id', count='exact') \
            .eq('entity_type', 'comment') \
            .execute()

        return {
            'total_chunks': chunks_response.count or 0,
            'total_embeddings': embeddings_response.count or 0,
            'comment_chunks': comment_chunks_response.count or 0
        }

    except Exception as e:
        logger.error("Failed to get RAG stats: %s", e)
        return {
            'total_chunks': 0,
            'total_embeddings': 0,
            'comment_chunks': 0
        }
