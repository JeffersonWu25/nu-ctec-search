"""
Database operations for unified RAG (rag_chunks + rag_embeddings).

Supports both comment-based and catalog-based chunks for discovery.
"""

import json
from typing import Dict, List, Any, Optional
from ..supabase_client import supabase


def fetch_comments_for_rag(page_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch all comments with full context for RAG chunk creation.

    Returns comments joined with course_offerings, courses, and instructors.

    Args:
        page_size: Number of rows per page (max 1000)

    Returns:
        List of comment dicts with nested context data.
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


def fetch_courses_for_rag(page_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch all courses with department info for catalog RAG chunks.

    Args:
        page_size: Number of rows per page (max 1000)

    Returns:
        List of course dicts with department data.
    """
    all_courses = []
    offset = 0

    while True:
        response = supabase.table('courses').select(
            'id, code, title, description, prerequisites_text, '
            'departments(id, code, name)'
        ).range(offset, offset + page_size - 1).execute()

        batch = response.data or []
        all_courses.extend(batch)

        if len(batch) < page_size:
            break

        offset += page_size

    return all_courses


def fetch_existing_rag_chunk_keys(
    entity_type: str,
    chunk_type: str,
    key_field: str = 'comment_id',
    page_size: int = 1000
) -> set:
    """
    Fetch existing rag_chunk keys for idempotency checking.

    Args:
        entity_type: 'course_offering' or 'course'
        chunk_type: 'comment', 'catalog_description', or 'catalog_prereqs'
        key_field: Metadata field to extract (e.g., 'comment_id', 'course_id')
        page_size: Number of rows per page

    Returns:
        Set of existing key values (UUIDs as strings).
    """
    existing_keys = set()
    offset = 0

    while True:
        response = supabase.table('rag_chunks').select(
            'metadata'
        ).eq('entity_type', entity_type).eq(
            'chunk_type', chunk_type
        ).range(offset, offset + page_size - 1).execute()

        batch = response.data or []

        for row in batch:
            metadata = row.get('metadata', {})
            key_value = metadata.get(key_field)
            if key_value:
                existing_keys.add(key_value)

        if len(batch) < page_size:
            break

        offset += page_size

    return existing_keys


def fetch_existing_catalog_chunks(page_size: int = 1000) -> Dict[str, set]:
    """
    Fetch existing catalog chunk types per course for idempotency.

    Returns:
        Dict mapping course_id -> set of existing chunk_types
    """
    existing = {}
    offset = 0

    while True:
        response = supabase.table('rag_chunks').select(
            'entity_id, chunk_type'
        ).eq('entity_type', 'course').in_(
            'chunk_type', ['catalog_description', 'catalog_prereqs']
        ).range(offset, offset + page_size - 1).execute()

        batch = response.data or []

        for row in batch:
            entity_id = row['entity_id']
            chunk_type = row['chunk_type']
            if entity_id not in existing:
                existing[entity_id] = set()
            existing[entity_id].add(chunk_type)

        if len(batch) < page_size:
            break

        offset += page_size

    return existing


def insert_rag_chunks(
    chunk_records: List[Dict[str, Any]],
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Insert rag_chunk records in batches.

    Args:
        chunk_records: List of dicts with entity_type, entity_id, chunk_type,
                      content, metadata
        batch_size: Records per batch

    Returns:
        Dict with 'inserted' count and 'errors' list
    """
    results = {
        'total': len(chunk_records),
        'inserted': 0,
        'errors': []
    }

    if not chunk_records:
        return results

    for i in range(0, len(chunk_records), batch_size):
        batch = chunk_records[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        try:
            response = supabase.table('rag_chunks').insert(batch).execute()
            inserted_count = len(response.data) if response.data else len(batch)
            results['inserted'] += inserted_count

        except Exception as e:
            results['errors'].append(f"Batch {batch_num}: {e}")

    return results


def fetch_rag_chunks_without_embeddings(
    limit: Optional[int] = None,
    page_size: int = 1000
) -> List[Dict[str, Any]]:
    """
    Fetch rag_chunks that don't have embeddings yet.

    Uses left outer join pattern to find unembedded chunks.

    Args:
        limit: Max chunks to return (None for all)
        page_size: Number of rows per page

    Returns:
        List of chunk dicts with id and content
    """
    all_chunks = []
    offset = 0

    while True:
        response = supabase.table('rag_chunks').select(
            'id, content, rag_embeddings(chunk_id)'
        ).is_('rag_embeddings.chunk_id', 'null').range(
            offset, offset + page_size - 1
        ).execute()

        batch = response.data or []

        for row in batch:
            # Double-check that there's no embedding
            emb_data = row.get('rag_embeddings')
            if emb_data is None or len(emb_data) == 0:
                all_chunks.append({'id': row['id'], 'content': row['content']})

                if limit and len(all_chunks) >= limit:
                    return all_chunks

        if len(batch) < page_size:
            break

        offset += page_size

    return all_chunks


def insert_rag_embeddings(
    embedding_records: List[Dict[str, Any]],
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Insert rag_embedding records in batches.

    Uses upsert with on_conflict to handle re-runs safely.

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
            response = supabase.table('rag_embeddings').upsert(
                batch,
                on_conflict='chunk_id'
            ).execute()

            inserted_count = len(response.data) if response.data else len(batch)
            results['inserted'] += inserted_count

        except Exception as e:
            results['errors'].append(f"Batch {batch_num}: {e}")

    return results
