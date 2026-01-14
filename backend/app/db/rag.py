"""
# DEPRECATED: comment_chunks + embeddings
# Superseded by rag_chunks + rag_embeddings.
# Use db/unified_rag.py instead.

Database operations for RAG (Retrieval-Augmented Generation).

Handles comment_chunks and embeddings table operations.
"""

import json
from typing import Dict, List, Any, Optional
from ..supabase_client import supabase


def fetch_comments_with_context(page_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch all comments with their course offering, course, and instructor context.

    Paginates through all results since Supabase has a default 1000 row limit.

    Args:
        page_size: Number of rows per page (max 1000)

    Returns:
        List of comment dicts with nested course_offerings, courses, instructors data.
    """
    all_comments = []
    offset = 0

    while True:
        response = supabase.table('comments').select(
            'id, content, course_offering_id, '
            'course_offerings!inner('
            '  id, year, quarter, section, course_id, instructor_id, '
            '  courses!inner(id, code, title), '
            '  instructors!inner(id, name)'
            ')'
        ).range(offset, offset + page_size - 1).execute()

        batch = response.data or []
        all_comments.extend(batch)

        if len(batch) < page_size:
            break

        offset += page_size

    return all_comments


def upsert_comment_chunks(
    chunk_records: List[Dict[str, Any]],
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Upsert chunk records into comment_chunks table in batches.

    Uses composite unique constraint (comment_id, chunk_index) for conflict resolution.

    Args:
        chunk_records: List of chunk dicts with comment_id, course_offering_id,
                      chunk_index, content, metadata
        batch_size: Records per batch

    Returns:
        Dict with 'upserted' count and 'errors' list
    """
    results = {
        'total': len(chunk_records),
        'upserted': 0,
        'errors': []
    }

    if not chunk_records:
        return results

    for i in range(0, len(chunk_records), batch_size):
        batch = chunk_records[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        try:
            response = supabase.table('comment_chunks').upsert(
                batch,
                on_conflict='comment_id,chunk_index'
            ).execute()

            upserted_count = len(response.data) if response.data else len(batch)
            results['upserted'] += upserted_count

        except Exception as e:
            results['errors'].append(f"Batch {batch_num}: {e}")

    return results


def fetch_chunks_without_embeddings(
    limit: Optional[int] = None,
    page_size: int = 1000
) -> List[Dict[str, Any]]:
    """
    Fetch comment_chunks that don't have embeddings yet.

    Paginates through results since Supabase has a default 1000 row limit.

    Args:
        limit: Max chunks to return (None for all)
        page_size: Number of rows per page (max 1000)

    Returns:
        List of chunk dicts with id and content
    """
    all_chunks = []
    offset = 0

    while True:
        query = supabase.table('comment_chunks').select(
            'id, content, embeddings(chunk_id)'
        ).is_('embeddings.chunk_id', 'null').range(offset, offset + page_size - 1)

        response = query.execute()
        batch = response.data or []

        for row in batch:
            if row.get('embeddings') is None or len(row.get('embeddings', [])) == 0:
                all_chunks.append({'id': row['id'], 'content': row['content']})

                if limit and len(all_chunks) >= limit:
                    return all_chunks

        if len(batch) < page_size:
            break

        offset += page_size

    return all_chunks


def insert_embeddings(
    embedding_records: List[Dict[str, Any]],
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Insert embedding records into embeddings table.

    Args:
        embedding_records: List of dicts with chunk_id, embedding, model
        batch_size: Records per batch

    Returns:
        Dict with 'inserted' count and 'errors' list
    """
    results = {
        'total': len(embedding_records),
        'inserted': 0,
        'errors': []
    }

    if not embedding_records:
        return results

    for i in range(0, len(embedding_records), batch_size):
        batch = embedding_records[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        try:
            response = supabase.table('embeddings').upsert(
                batch,
                on_conflict='chunk_id'
            ).execute()

            inserted_count = len(response.data) if response.data else len(batch)
            results['inserted'] += inserted_count

        except Exception as e:
            results['errors'].append(f"Batch {batch_num}: {e}")

    return results


def fetch_chunks_with_embeddings_for_offering(
    course_offering_id: str
) -> List[Dict[str, Any]]:
    """
    Fetch all chunks and their embeddings for a course offering.

    Used for Python-side similarity computation during MVP iteration.

    Args:
        course_offering_id: UUID of the course offering

    Returns:
        List of dicts with: id, comment_id, content, metadata, embedding
    """
    response = supabase.table('comment_chunks').select(
        'id, comment_id, content, metadata, embeddings(embedding)'
    ).eq('course_offering_id', course_offering_id).execute()

    results = []
    for row in response.data or []:
        # Skip chunks without embeddings
        embeddings_data = row.get('embeddings')
        if not embeddings_data:
            continue

        # Handle both single object and array responses
        if isinstance(embeddings_data, list):
            if len(embeddings_data) == 0:
                continue
            embedding = embeddings_data[0].get('embedding')
        else:
            embedding = embeddings_data.get('embedding')

        if embedding:
            # Parse embedding string to list of floats (Supabase returns vector as string)
            if isinstance(embedding, str):
                embedding = json.loads(embedding)

            results.append({
                'id': row['id'],
                'comment_id': row['comment_id'],
                'content': row['content'],
                'metadata': row['metadata'],
                'embedding': embedding
            })

    return results
