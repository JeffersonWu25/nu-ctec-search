"""
Department table database operations.

All Supabase department table interactions go here.
"""

from typing import Dict, List, Optional
from ..supabase_client import supabase
from .batch_helpers import batch_upsert, create_lookup_map


def get_all_departments() -> List[Dict]:
    """
    Get all departments from the database.
    
    Returns:
        List of department records with id, code, name
    """
    try:
        response = supabase.table('departments').select('*').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch departments: {e}")
        return []


def get_departments_lookup() -> Dict[str, str]:
    """
    Get departments as lookup map: code -> id.
    
    Returns:
        Dictionary mapping department code to department id
    """
    return create_lookup_map('departments', 'code', 'id')


def get_department_by_code(code: str) -> Optional[Dict]:
    """
    Get a single department by its code.
    
    Args:
        code: Department code (e.g., 'COMP_SCI')
        
    Returns:
        Department record or None if not found
    """
    try:
        response = supabase.table('departments').select('*').eq('code', code).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to fetch department {code}: {e}")
        return None


def upsert_departments(departments: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert departments in batches.
    
    Args:
        departments: List of department records
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='departments',
        data=departments,
        conflict_key='code',
        batch_size=batch_size,
        description='departments'
    )


def create_department(code: str, name: str) -> Optional[Dict]:
    """
    Create a single department.
    
    Args:
        code: Department code
        name: Department name
        
    Returns:
        Created department record or None if failed
    """
    try:
        department = {'code': code, 'name': name}
        response = supabase.table('departments').insert(department).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to create department {code}: {e}")
        return None


def delete_department(department_id: str) -> bool:
    """
    Delete a department by ID.
    
    Args:
        department_id: UUID of the department
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table('departments').delete().eq('id', department_id).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to delete department {department_id}: {e}")
        return False