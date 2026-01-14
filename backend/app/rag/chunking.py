"""
Chunking utilities for RAG operations.

Provides helpers for building metadata dicts and preparing comment chunks.
"""

from typing import Dict, Any, Optional, TypedDict


class ChunkContext(TypedDict):
    """Context data needed to build chunk metadata."""
    course_offering_id: str
    course_id: str
    course_code: str
    course_title: str
    year: int
    quarter: str
    section: Optional[int]
    instructor_id: str
    instructor_name: str


def build_chunk_metadata(context: ChunkContext) -> Dict[str, Any]:
    """
    Build metadata dict for a comment chunk.

    This metadata is stored in comment_chunks.metadata for:
    - Future discovery features (cross-offering search)
    - Citation display in the UI

    Args:
        context: ChunkContext with all required fields

    Returns:
        Metadata dict ready for JSONB storage
    """
    return {
        "course_offering_id": context["course_offering_id"],
        "course_id": context["course_id"],
        "course_code": context["course_code"],
        "course_title": context["course_title"],
        "year": context["year"],
        "quarter": context["quarter"],
        "section": context["section"],
        "instructor_id": context["instructor_id"],
        "instructor_name": context["instructor_name"],
    }


def build_chunk_record(
    comment_id: str,
    course_offering_id: str,
    content: str,
    metadata: Dict[str, Any],
    chunk_index: int = 0,
) -> Dict[str, Any]:
    """
    Build a complete comment_chunks record for upsert.

    Args:
        comment_id: UUID of the source comment
        course_offering_id: UUID of the course offering (direct FK)
        content: The comment text
        metadata: Metadata dict from build_chunk_metadata()
        chunk_index: Index of this chunk (0 for 1:1 mapping)

    Returns:
        Record dict ready for upsert into comment_chunks
    """
    return {
        "comment_id": comment_id,
        "course_offering_id": course_offering_id,
        "chunk_index": chunk_index,
        "content": content,
        "metadata": metadata,
    }
