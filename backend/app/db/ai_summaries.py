"""
AI summaries database operations.

Handles CRUD operations for AI summaries with staleness detection.
"""

from typing import Dict, List, Optional
from datetime import datetime
from ..supabase_client import supabase
from ..utils.logging import get_job_logger


def get_stale_course_offerings() -> List[Dict]:
    """
    Get course_offerings that need AI summary updates.

    Returns offerings where:
    - No summary exists, OR
    - Summary's source_updated_at < max(comments.created_at) for that offering
    """
    logger = get_job_logger('ai_summaries')
    
    try:
        response = supabase.rpc("get_stale_course_offerings").execute()
        rows = response.data
        if rows:
            logger.info("Found %d stale course offerings", len(rows))
            return rows
        return []
    except Exception as e:
        logger.error("Failed to get stale course offerings: %s", e)
        return []


def get_stale_instructors(affected_instructor_ids: Optional[List[str]] = None) -> List[Dict]:
    """
    Get instructors that need AI summary updates.

    Args:
        affected_instructor_ids: If provided, only check these instructors

    Returns instructors where:
    - No summary exists, OR
    - Summary's source_updated_at < max(comments.created_at) across all their offerings
    """
    logger = get_job_logger('ai_summaries')

    
    try:
        if affected_instructor_ids:
            response = supabase.rpc("get_stale_instructors", {
                "affected_instructor_ids": affected_instructor_ids
            }).execute()
        else:
            response = supabase.rpc("get_stale_instructors").execute()
        
        rows = response.data
        if rows:
            logger.info("Found %d stale instructors", len(rows))
            return rows
        return []
    except Exception as e:
        logger.error("Failed to get stale instructors: %s", e)
        return []


def get_stale_courses(affected_course_ids: Optional[List[str]] = None) -> List[Dict]:
    """
    Get courses that need AI summary updates.

    Args:
        affected_course_ids: If provided, only check these courses

    Returns courses where:
    - No summary exists, OR
    - Summary's source_updated_at < max(updated_at) of course_offering summaries for that course
    """
    logger = get_job_logger('ai_summaries')

    
    try:
        if affected_course_ids:
            response = supabase.rpc("get_stale_courses", {
                "affected_course_ids": affected_course_ids
            }).execute()
        else:
            response = supabase.rpc("get_stale_courses").execute()
        
        rows = response.data
        if rows:
            logger.info("Found %d stale courses", len(rows))
            return rows
        return []
    except Exception as e:
        logger.error("Failed to get stale courses: %s", e)
        return []


def get_comments_for_offering(offering_id: str) -> List[str]:
    """Get all comment content for a specific course offering."""
    try:
        response = supabase.table('comments') \
            .select('content') \
            .eq('course_offering_id', offering_id) \
            .execute()
        
        return [row['content'] for row in response.data]
    except Exception as e:
        logger = get_job_logger('ai_summaries')
        logger.error("Failed to get comments for offering %s: %s", offering_id, e)
        return []


def get_comments_for_instructor(instructor_id: str) -> List[Dict]:
    """
    Get all comments for an instructor across all their offerings.
    Returns structured data with offering context.
    """
    logger = get_job_logger('ai_summaries')
    try:
        # First get the offering IDs for this instructor
        offering_response = supabase.table('course_offerings') \
            .select('id, course_id, quarter, year, section, courses(code, title)') \
            .eq('instructor_id', instructor_id) \
            .execute()
        
        if not offering_response.data:
            logger.info("No offerings found for instructor %s", instructor_id)
            return []
            
        # Extract offering IDs and build offering lookup
        offering_ids = [row['id'] for row in offering_response.data]
        offering_lookup = {row['id']: row for row in offering_response.data}
        
        # Now get comments for these offerings
        comments_response = supabase.table('comments') \
            .select('content, course_offering_id') \
            .in_('course_offering_id', offering_ids) \
            .execute()
        
        if not comments_response.data:
            logger.info("No comments found for instructor %s offerings", instructor_id)
            return []
        
        # Combine comment data with offering context
        result = []
        for comment in comments_response.data:
            offering_id = comment['course_offering_id']
            offering_info = offering_lookup.get(offering_id)
            if offering_info:
                result.append({
                    'content': comment['content'],
                    'course_offering_id': offering_id,
                    'course_offerings': {
                        'course_id': offering_info['course_id'],
                        'quarter': offering_info['quarter'],
                        'year': offering_info['year'],
                        'section': offering_info['section'],
                        'courses': offering_info['courses']
                    }
                })
        
        logger.info("Found %d comments for instructor %s", len(result), instructor_id[:8])
        return result
        
    except Exception as e:
        logger.error("Failed to get comments for instructor %s: %s", instructor_id, e)
        return []


def get_offering_summaries_for_course(course_id: str) -> List[str]:
    """Get all course_offering summaries for a specific course."""
    logger = get_job_logger('ai_summaries')
    try:
        # First get the offering IDs for this course
        offering_response = supabase.table('course_offerings') \
            .select('id') \
            .eq('course_id', course_id) \
            .execute()
        
        if not offering_response.data:
            return []
            
        # Extract just the UUID strings from the response
        offering_ids = [row['id'] for row in offering_response.data]
        
        if not offering_ids:
            return []
        
        # Now get the summaries for these offerings
        response = supabase.table('ai_summaries') \
            .select('summary') \
            .eq('entity_type', 'course_offering') \
            .eq('summary_type', 'default') \
            .in_('entity_id', offering_ids) \
            .execute()
        
        return [row['summary'] for row in response.data]
    except Exception as e:
        logger.error("Failed to get offering summaries for course %s: %s", course_id, e)
        return []


def upsert_ai_summary(
    entity_type: str,
    entity_id: str, 
    summary: str,
    model: str,
    prompt: str,
    source_updated_at: datetime,
    source_comment_count: Optional[int] = None,
    summary_type: str = 'default'
) -> Dict:
    """
    Upsert an AI summary record.
    
    Args:
        entity_type: Type of entity ('course', 'instructor', 'course_offering')
        entity_id: UUID of the entity
        summary: The generated summary text
        model: Model used for generation (e.g., 'gpt-4')
        prompt: Prompt used for generation
        source_updated_at: Timestamp of newest underlying data
        source_comment_count: Number of comments used (if applicable)
        summary_type: Type of summary ('default', 'short', 'detailed')
    
    Returns:
        Dictionary with success status and any errors
    """
    logger = get_job_logger('ai_summaries')
    
    try:
        data = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'summary_type': summary_type,
            'summary': summary,
            'model': model,
            'prompt': prompt,
            'source_updated_at': source_updated_at.isoformat(),
            'source_comment_count': source_comment_count,
            'generated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase.table('ai_summaries').upsert(data).execute()
        
        logger.info("Upserted %s summary for %s", entity_type, entity_id)
        return {'success': True, 'data': response.data}
        
    except Exception as e:
        logger.error("Failed to upsert %s summary for %s: %s", entity_type, entity_id, e)
        return {'success': False, 'error': str(e)}


def delete_ai_summaries(entity_type: str, entity_ids: List[str]) -> Dict:
    """Delete AI summaries for given entities."""
    logger = get_job_logger('ai_summaries')
    
    try:
        supabase.table('ai_summaries') \
            .delete() \
            .eq('entity_type', entity_type) \
            .in_('entity_id', entity_ids) \
            .execute()

        logger.info("Deleted %d %s summaries", len(entity_ids), entity_type)
        return {'success': True, 'deleted_count': len(entity_ids)}
        
    except Exception as e:
        logger.error("Failed to delete %s summaries: %s", entity_type, e)
        return {'success': False, 'error': str(e)}


def get_existing_summary(entity_type: str, entity_id: str, summary_type: str = 'default') -> Optional[Dict]:
    """Get an existing AI summary if it exists."""
    try:
        response = supabase.table('ai_summaries') \
            .select('*') \
            .eq('entity_type', entity_type) \
            .eq('entity_id', entity_id) \
            .eq('summary_type', summary_type) \
            .execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        logger = get_job_logger('ai_summaries')
        logger.error("Failed to get existing summary for %s %s: %s", entity_type, entity_id, e)
        return None
