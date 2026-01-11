"""
Reusable batch operation helpers for Supabase operations.

Consolidates common patterns from upload scripts.
"""

from typing import Dict, List, Any, Optional
from ..supabase_client import supabase
from ..settings import settings

def create_lookup_map(table_name: str, key_field: str, value_field: str) -> Dict[str, Any]:
    """
    Create a lookup map from a database table.
    
    Args:
        table_name: Name of the table
        key_field: Field to use as key
        value_field: Field to use as value
        
    Returns:
        Dictionary mapping key_field -> value_field
    """
    try:
        response = supabase.table(table_name).select(f"{key_field}, {value_field}").execute()
        return {item[key_field]: item[value_field] for item in response.data}
    except Exception as e:
        print(f"❌ Failed to create lookup map for {table_name}: {e}")
        return {}

def batch_upsert(
    table_name: str,
    data: List[Dict],
    conflict_key: str,
    batch_size: Optional[int] = None,
    description: str = "records"
) -> Dict[str, Any]:
    """
    Upsert data in batches to a Supabase table.
    
    Args:
        table_name: Name of the target table
        data: List of records to upsert
        conflict_key: Key to use for conflict resolution
        batch_size: Size of each batch (uses default if None)
        description: Description for logging
        
    Returns:
        Dictionary with results: {'uploaded': int, 'errors': List[str]}
    """
    if batch_size is None:
        batch_size = settings.DEFAULT_BATCH_SIZE
    
    results = {
        'total': len(data),
        'uploaded': 0,
        'errors': []
    }
    
    if not data:
        return results
    
    print(f"📤 Upserting {len(data)} {description} to {table_name} in batches of {batch_size}")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} {description})")
        
        try:
            response = supabase.table(table_name).upsert(
                batch,
                on_conflict=conflict_key
            ).execute()
            
            uploaded_count = len(response.data) if response.data else len(batch)
            results['uploaded'] += uploaded_count
            
            print(f"   ✅ Uploaded {uploaded_count} {description}")
            
        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
    
    return results

def batch_update(
    table_name: str,
    updates: List[Dict],
    id_field: str = 'id',
    batch_size: Optional[int] = None,
    description: str = "records"
) -> Dict[str, Any]:
    """
    Update records in batches with transaction safety.
    
    Args:
        table_name: Name of the target table
        updates: List of update records (must include id_field)
        id_field: Field to use for identifying records to update
        batch_size: Size of each batch
        description: Description for logging
        
    Returns:
        Dictionary with results: {'updated': int, 'errors': List[str]}
    """
    if batch_size is None:
        batch_size = settings.DEFAULT_BATCH_SIZE
    
    results = {
        'total': len(updates),
        'updated': 0,
        'errors': []
    }
    
    if not updates:
        return results
    
    print(f"🔄 Updating {len(updates)} {description} in {table_name}")
    
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(updates) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} {description})")
        
        try:
            # Use upsert for atomic batch operations instead of individual updates
            upsert_data = []
            for update_record in batch:
                upsert_data.append(update_record)
            
            response = supabase.table(table_name).upsert(
                upsert_data,
                on_conflict=id_field
            ).execute()
            
            batch_updated = len(response.data) if response.data else len(batch)
            results['updated'] += batch_updated
            
            print(f"   ✅ Updated {batch_updated} {description}")
            
        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
    
    return results

def batch_delete(
    table_name: str,
    condition_field: str,
    condition_values: List[Any],
    batch_size: Optional[int] = None,
    description: str = "records"
) -> Dict[str, Any]:
    """
    Delete records in batches based on field values.
    
    Args:
        table_name: Name of the target table
        condition_field: Field to match for deletion
        condition_values: Values to delete
        batch_size: Size of each batch
        description: Description for logging
        
    Returns:
        Dictionary with results: {'deleted': int, 'errors': List[str]}
    """
    if batch_size is None:
        batch_size = settings.DEFAULT_BATCH_SIZE
    
    results = {
        'total': len(condition_values),
        'deleted': 0,
        'errors': []
    }
    
    if not condition_values:
        return results
    
    print(f"🗑️  Deleting {len(condition_values)} {description} from {table_name}")
    
    try:
        for value in condition_values:
            supabase.table(table_name).delete().eq(condition_field, value).execute()
            results['deleted'] += 1
        
        print(f"   ✅ Deleted {results['deleted']} {description}")
        
    except Exception as e:
        error_msg = f"Delete operation failed: {str(e)}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results