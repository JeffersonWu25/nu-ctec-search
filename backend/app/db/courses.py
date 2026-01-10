"""
Course table database operations.

All Supabase course table interactions go here.
"""

from typing import Dict, List, Optional
from ..supabase_client import supabase
from .batch_helpers import batch_upsert, batch_update, create_lookup_map


def get_all_courses() -> List[Dict]:
    """
    Get all courses from the database.
    
    Returns:
        List of course records
    """
    try:
        response = supabase.table('courses').select('*').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch courses: {e}")
        return []


def get_courses_lookup() -> Dict[str, str]:
    """
    Get courses as lookup map: code -> id.
    
    Returns:
        Dictionary mapping course code to course id
    """
    return create_lookup_map('courses', 'code', 'id')


def get_courses_without_department_id() -> List[Dict]:
    """
    Get all courses that don't have a department_id set.
    
    Returns:
        List of course records missing department_id
    """
    try:
        response = supabase.table('courses').select('id, code').is_('department_id', 'null').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch courses without department_id: {e}")
        return []


def get_courses_with_empty_catalog_data() -> List[Dict]:
    """
    Get all courses that have empty catalog data (description, prerequisites, and no requirements).
    
    Returns:
        List of course records with empty catalog data
    """
    try:
        # Get courses with empty or null description AND empty or null prerequisites_text
        response = supabase.table('courses').select('''
            id, code, description, prerequisites_text
        ''').or_(
            'description.is.null,description.eq.'
        ).or_(
            'prerequisites_text.is.null,prerequisites_text.eq.'
        ).execute()
        
        courses = response.data
        
        # Further filter to courses with no requirements
        courses_with_no_requirements = []
        for course in courses:
            # Check if course has any requirements
            req_response = supabase.table('course_requirements').select('id').eq(
                'course_id', course['id']
            ).limit(1).execute()
            
            # Include if both description and prerequisites are empty AND no requirements
            desc_empty = not course.get('description') or course['description'].strip() == ''
            prereq_empty = not course.get('prerequisites_text') or course['prerequisites_text'].strip() == ''
            no_requirements = len(req_response.data) == 0
            
            if desc_empty and prereq_empty and no_requirements:
                courses_with_no_requirements.append(course)
        
        return courses_with_no_requirements
        
    except Exception as e:
        print(f"❌ Failed to fetch courses with empty catalog data: {e}")
        return []


def get_course_by_code(code: str) -> Optional[Dict]:
    """
    Get a single course by its code.
    
    Args:
        code: Course code (e.g., 'COMP_SCI_214')
        
    Returns:
        Course record or None if not found
    """
    try:
        response = supabase.table('courses').select('*').eq('code', code).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to fetch course {code}: {e}")
        return None


def upsert_courses(courses: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert courses in batches.
    
    Args:
        courses: List of course records
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='courses',
        data=courses,
        conflict_key='code',
        batch_size=batch_size,
        description='courses'
    )


def update_course_descriptions(course_updates: List[Dict], batch_size: int = 100) -> Dict:
    """
    Update course descriptions and prerequisites in batches.
    
    Args:
        course_updates: List of update records with id, description, prerequisites_text
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with update results: {'total', 'updated', 'errors'}
    """
    return batch_update(
        table_name='courses',
        updates=course_updates,
        id_field='id',
        batch_size=batch_size,
        description='course catalog data (descriptions + prerequisites)'
    )


def update_course_department_id(course_id: str, department_id: str) -> bool:
    """
    Update a single course's department_id.
    
    Args:
        course_id: UUID of the course
        department_id: UUID of the department
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table('courses').update({'department_id': department_id}).eq('id', course_id).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to update course {course_id} department: {e}")
        return False


def update_courses_department_mapping(course_department_updates: List[Dict], batch_size: int = 100) -> Dict:
    """
    Update multiple courses' department_id in batches.
    
    Args:
        course_department_updates: List of updates with 'id' and 'department_id'
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with update results: {'total', 'updated', 'errors'}
    """
    return batch_update(
        table_name='courses',
        updates=course_department_updates,
        id_field='id',
        batch_size=batch_size,
        description='course departments'
    )


def create_course(code: str, title: str, department_id: Optional[str] = None) -> Optional[Dict]:
    """
    Create a single course.
    
    Args:
        code: Course code
        title: Course title
        department_id: Optional department UUID
        
    Returns:
        Created course record or None if failed
    """
    try:
        course = {'code': code, 'title': title}
        if department_id:
            course['department_id'] = department_id
            
        response = supabase.table('courses').insert(course).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to create course {code}: {e}")
        return None


def delete_course(course_id: str) -> bool:
    """
    Delete a course by ID.
    
    Args:
        course_id: UUID of the course
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table('courses').delete().eq('id', course_id).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to delete course {course_id}: {e}")
        return False