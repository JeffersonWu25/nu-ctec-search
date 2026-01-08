"""
Requirements table database operations.

All Supabase requirements table interactions go here.
"""

from typing import Dict, List, Optional, Set
from ..supabase_client import supabase
from .batch_helpers import batch_upsert, create_lookup_map, batch_delete


def get_all_requirements() -> List[Dict]:
    """
    Get all requirements from the database.
    
    Returns:
        List of requirement records with id, name
    """
    try:
        response = supabase.table('requirements').select('*').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch requirements: {e}")
        return []


def get_requirements_lookup() -> Dict[str, str]:
    """
    Get requirements as lookup map: name -> id.
    
    Returns:
        Dictionary mapping requirement name to requirement id
    """
    return create_lookup_map('requirements', 'name', 'id')


def get_requirement_by_name(name: str) -> Optional[Dict]:
    """
    Get a single requirement by its name.
    
    Args:
        name: Requirement name
        
    Returns:
        Requirement record or None if not found
    """
    try:
        response = supabase.table('requirements').select('*').eq('name', name).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to fetch requirement {name}: {e}")
        return None


def upsert_requirements(requirements: List[Dict], batch_size: int = 200) -> Dict:
    """
    Upsert requirements in batches.
    
    Args:
        requirements: List of requirement records with 'name' field
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='requirements',
        data=requirements,
        conflict_key='name',
        batch_size=batch_size,
        description='requirements'
    )


def upsert_requirements_from_names(requirement_names: Set[str], batch_size: int = 200) -> Dict:
    """
    Create requirements from a set of names.
    
    Args:
        requirement_names: Set of requirement names
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results and lookup map: {'total', 'uploaded', 'errors', 'lookup_map'}
    """
    if not requirement_names:
        return {'total': 0, 'uploaded': 0, 'errors': [], 'lookup_map': {}}
    
    # Convert names to requirement records
    requirements = [{'name': name} for name in requirement_names if name.strip()]
    
    # Upsert requirements
    results = upsert_requirements(requirements, batch_size)
    
    # Build updated lookup map
    lookup_map = get_requirements_lookup()
    results['lookup_map'] = lookup_map
    
    return results


def create_requirement(name: str) -> Optional[Dict]:
    """
    Create a single requirement.
    
    Args:
        name: Requirement name
        
    Returns:
        Created requirement record or None if failed
    """
    try:
        requirement = {'name': name}
        response = supabase.table('requirements').insert(requirement).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to create requirement {name}: {e}")
        return None


def delete_requirement(requirement_id: str) -> bool:
    """
    Delete a requirement by ID.
    
    Args:
        requirement_id: UUID of the requirement
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table('requirements').delete().eq('id', requirement_id).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to delete requirement {requirement_id}: {e}")
        return False


# Course-Requirements Junction Table Operations

def get_course_requirements(course_id: str) -> List[Dict]:
    """
    Get all requirements for a specific course.
    
    Args:
        course_id: UUID of the course
        
    Returns:
        List of course_requirements junction records
    """
    try:
        response = supabase.table('course_requirements').select('*').eq('course_id', course_id).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch requirements for course {course_id}: {e}")
        return []


def clear_course_requirements(course_ids: List[str]) -> Dict:
    """
    Remove all requirements for specified courses.
    
    Args:
        course_ids: List of course UUIDs
        
    Returns:
        Dictionary with deletion results: {'total', 'deleted', 'errors'}
    """
    return batch_delete(
        table_name='course_requirements',
        condition_field='course_id',
        condition_values=course_ids,
        description='course requirements'
    )


def upsert_course_requirements(course_requirement_pairs: List[Dict], batch_size: int = 500) -> Dict:
    """
    Upsert course-requirement associations in batches.
    
    Args:
        course_requirement_pairs: List of records with 'course_id' and 'requirement_id'
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='course_requirements',
        data=course_requirement_pairs,
        conflict_key='course_id,requirement_id',
        batch_size=batch_size,
        description='course-requirement links'
    )


def update_course_requirements(course_ids: List[str], course_requirement_pairs: List[Dict]) -> Dict:
    """
    Replace all requirements for specified courses (delete old + insert new).
    
    Args:
        course_ids: List of course UUIDs to update
        course_requirement_pairs: New course-requirement associations
        
    Returns:
        Dictionary with operation results: {'cleared', 'linked', 'errors'}
    """
    results = {'cleared': 0, 'linked': 0, 'errors': []}
    
    # Clear existing requirements
    clear_results = clear_course_requirements(course_ids)
    results['cleared'] = clear_results.get('deleted', 0)
    results['errors'].extend(clear_results.get('errors', []))
    
    # Add new requirements
    if course_requirement_pairs:
        link_results = upsert_course_requirements(course_requirement_pairs)
        results['linked'] = link_results.get('uploaded', 0)
        results['errors'].extend(link_results.get('errors', []))
    
    return results