#!/usr/bin/env python3
"""
Upload course catalog data from JSON to Supabase database.

This module handles bulk uploading of scraped course catalog data following
the ETL best practices pipeline: JSON artifact → database upload.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from api.supabase_client import supabase


def load_catalog_data(file_path: str) -> List[Dict]:
    """Load catalog data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📂 Loaded {len(data)} courses from {file_path}")
        return data
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def validate_catalog_data(catalog_data: List[Dict]) -> bool:
    """Validate catalog data structure."""
    if not catalog_data or not isinstance(catalog_data, list):
        print("❌ Invalid data: expected list of courses")
        return False
    
    required_fields = ['course_code', 'description', 'prerequisites_text', 'requirements']
    
    for i, course in enumerate(catalog_data[:5]):  # Check first 5 courses
        for field in required_fields:
            if field not in course:
                print(f"❌ Missing field '{field}' in course {i+1}")
                return False
    
    print(f"✅ Data validation passed")
    return True


def build_lookup_maps() -> Dict[str, Dict]:
    """Build lookup maps for courses and requirements only."""
    print("🗃️  Building lookup maps...")
    
    # Fetch all existing courses (id, code) - this is our filter
    print("   Fetching existing courses...")
    courses_response = supabase.table('courses').select('id, code').execute()
    courses_map = {course['code']: course['id'] for course in courses_response.data}
    
    # Fetch all requirements  
    print("   Fetching requirements...")
    requirements_response = supabase.table('requirements').select('id, name').execute()
    requirements_map = {req['name']: req['id'] for req in requirements_response.data}
    
    print(f"   📚 Found {len(courses_map)} existing courses in database")
    print(f"   📋 Found {len(requirements_map)} existing requirements")  
    
    return {
        'courses': courses_map,
        'requirements': requirements_map
    }


def extract_unique_requirements(catalog_data: List[Dict]) -> Set[str]:
    """Extract all unique requirement names from catalog data."""
    all_requirements = set()
    for course in catalog_data:
        all_requirements.update(course.get('requirements', []))
    
    # Remove empty strings
    all_requirements.discard('')
    return all_requirements


def upsert_requirements(requirements: Set[str], batch_size: int = 200) -> Dict[str, str]:
    """Upsert requirements and return updated lookup map."""
    if not requirements:
        return {}
    
    print(f"📋 Upserting {len(requirements)} requirements...")
    
    # Convert to list for batching
    requirements_list = [{'name': req} for req in requirements]
    
    # Process in batches
    updated_map = {}
    for i in range(0, len(requirements_list), batch_size):
        batch = requirements_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(requirements_list) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} requirements)")
        
        try:
            response = supabase.table('requirements').upsert(
                batch, 
                on_conflict='name'
            ).execute()
            
            # Add to lookup map
            for req in response.data:
                updated_map[req['name']] = req['id']
                
        except Exception as e:
            print(f"   ❌ Batch {batch_num} failed: {str(e)}")
    
    print(f"   ✅ Upserted requirements")
    return updated_map


def filter_to_existing_courses(catalog_data: List[Dict], courses_map: Dict[str, str]) -> Dict:
    """Filter catalog data to only courses that exist in database."""
    print("🔍 Filtering catalog data to existing courses only...")
    
    matched_courses = []
    missing_courses = []
    
    for course_data in catalog_data:
        course_code = course_data['course_code']
        
        if course_code in courses_map:
            matched_courses.append(course_data)
        else:
            missing_courses.append(course_code)
    
    print(f"   ✅ {len(matched_courses)} courses found in database")
    print(f"   ❌ {len(missing_courses)} courses NOT found (will be skipped)")
    
    if missing_courses:
        print("   📝 Sample missing courses:")
        for course_code in missing_courses[:10]:
            print(f"      • {course_code}")
        if len(missing_courses) > 10:
            print(f"      ... and {len(missing_courses) - 10} more")
    
    return {
        'matched_data': matched_courses,
        'missing_courses': missing_courses
    }


def prepare_course_updates(matched_data: List[Dict], courses_map: Dict[str, str]) -> List[Dict]:
    """Prepare course update records for batch update."""
    print("🔄 Preparing course updates...")
    
    course_updates = []
    
    for course_data in matched_data:
        course_code = course_data['course_code']
        course_id = courses_map[course_code]
        
        # Prepare update record (ID + fields to update)
        update_record = {
            'id': course_id,
            'description': course_data['description'],
            'prerequisites_text': course_data['prerequisites_text']
        }
        
        course_updates.append(update_record)
    
    print(f"   ✅ Prepared {len(course_updates)} course updates")
    return course_updates


def batch_update_courses(course_updates: List[Dict], batch_size: int = 100) -> Dict:
    """Update existing courses in batches (UPDATE only, no inserts)."""
    if not course_updates:
        return {'updated': 0, 'errors': []}
    
    print(f"📚 Updating {len(course_updates)} existing courses...")
    
    results = {'updated': 0, 'errors': []}
    
    for i in range(0, len(course_updates), batch_size):
        batch = course_updates[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(course_updates) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} courses)")
        
        try:
            # Use update() for each course in batch since Supabase doesn't support batch UPDATE
            for course_update in batch:
                course_id = course_update['id']
                update_data = {
                    'description': course_update['description'],
                    'prerequisites_text': course_update['prerequisites_text']
                }
                
                supabase.table('courses').update(update_data).eq('id', course_id).execute()
                results['updated'] += 1
            
            print(f"   ✅ Updated {len(batch)} courses")
            
        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
    
    return results


def prepare_course_requirements(matched_data: List[Dict], lookup_maps: Dict) -> Dict:
    """Prepare course-requirements link data for matched courses only."""
    print("🔗 Preparing course-requirements links...")
    
    courses_map = lookup_maps['courses']
    requirements_map = lookup_maps['requirements']
    
    course_requirement_pairs = []
    matched_course_ids = set()
    
    for course_data in matched_data:
        course_code = course_data['course_code']
        course_id = courses_map[course_code]  # Safe since data is already filtered
        matched_course_ids.add(course_id)
        
        requirements = course_data.get('requirements', [])
        
        # Create pairs for each requirement
        for req_name in requirements:
            if req_name and req_name in requirements_map:
                course_requirement_pairs.append({
                    'course_id': course_id,
                    'requirement_id': requirements_map[req_name]
                })
    
    print(f"   ✅ Created {len(course_requirement_pairs)} course-requirement links")
    print(f"   📚 Links for {len(matched_course_ids)} matched courses")
    
    return {
        'pairs': course_requirement_pairs,
        'course_ids': list(matched_course_ids)
    }


def update_course_requirements(course_ids: List[str], course_requirement_pairs: List[Dict]) -> Dict:
    """Update course-requirements links for matched courses only (delete old + insert new)."""
    print("🔗 Updating course-requirements links...")
    
    results = {'linked': 0, 'errors': []}
    
    if not course_requirement_pairs:
        print("   No course-requirement links to update")
        return results
    
    try:
        # Delete existing requirements for updated courses only
        print(f"   Removing old requirements for {len(course_ids)} matched courses...")
        for course_id in course_ids:
            supabase.table('course_requirements').delete().eq('course_id', course_id).execute()
        
        # Insert new requirements in batches
        batch_size = 500
        for i in range(0, len(course_requirement_pairs), batch_size):
            batch = course_requirement_pairs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(course_requirement_pairs) + batch_size - 1) // batch_size
            
            print(f"   Inserting batch {batch_num}/{total_batches} ({len(batch)} links)")
            
            response = supabase.table('course_requirements').insert(batch).execute()
            linked_count = len(response.data) if response.data else len(batch)
            results['linked'] += linked_count
        
        print(f"   ✅ Linked {results['linked']} course-requirement pairs")
        
    except Exception as e:
        error_msg = f"Course-requirements update failed: {str(e)}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results


def upload_catalog_data(catalog_data: List[Dict], dry_run: bool = False) -> Dict[str, Any]:
    """
    Upload course catalog data to database (UPDATE ONLY - no inserts).
    
    Args:
        catalog_data: List of course dictionaries from JSON
        dry_run: If True, preview changes without applying
        
    Returns:
        Dictionary with upload results and statistics
    """
    print("📤 Starting catalog data upload (UPDATE ONLY MODE)...")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    # Step 1: Validate data
    if not validate_catalog_data(catalog_data):
        return {'error': 'Data validation failed'}
    
    # Step 2: Build lookup maps (courses and requirements only)
    lookup_maps = build_lookup_maps()
    
    # Step 3: Filter to existing courses only
    filter_results = filter_to_existing_courses(catalog_data, lookup_maps['courses'])
    matched_data = filter_results['matched_data']
    missing_courses = filter_results['missing_courses']
    
    if not matched_data:
        print("❌ No courses matched existing database records. Nothing to update.")
        return {
            'total_courses': len(catalog_data),
            'courses_matched': 0,
            'courses_updated': 0,
            'courses_missing': missing_courses,
            'requirements_found': 0,
            'requirements_linked': 0,
            'errors': [],
            'dry_run': dry_run
        }
    
    # Step 4: Upsert requirements for matched courses
    unique_requirements = extract_unique_requirements(matched_data)
    print(f"📋 Found {len(unique_requirements)} unique requirements in matched courses")
    
    if not dry_run and unique_requirements:
        updated_requirements = upsert_requirements(unique_requirements)
        # Update lookup map with new requirements
        lookup_maps['requirements'].update(updated_requirements)
    else:
        print("   [DRY RUN] Would upsert requirements")
    
    # Step 5: Prepare and update courses (EXISTING ONLY)
    course_updates = prepare_course_updates(matched_data, lookup_maps['courses'])
    
    if not dry_run:
        course_results = batch_update_courses(course_updates)
    else:
        print(f"   [DRY RUN] Would update {len(course_updates)} existing courses")
        course_results = {'updated': len(course_updates), 'errors': []}
    
    # Step 6: Prepare and update course-requirements (MATCHED COURSES ONLY)
    req_prep = prepare_course_requirements(matched_data, lookup_maps)
    
    if not dry_run:
        requirements_results = update_course_requirements(
            req_prep['course_ids'], 
            req_prep['pairs']
        )
    else:
        print(f"   [DRY RUN] Would link {len(req_prep['pairs'])} course-requirement pairs")
        requirements_results = {'linked': len(req_prep['pairs']), 'errors': []}
    
    # Compile results
    results = {
        'total_courses': len(catalog_data),
        'courses_matched': len(matched_data),
        'courses_updated': course_results['updated'],
        'courses_missing': missing_courses,
        'requirements_found': len(unique_requirements),
        'requirements_linked': requirements_results['linked'],
        'errors': course_results['errors'] + requirements_results['errors'],
        'dry_run': dry_run
    }
    
    return results


def print_upload_summary(results: Dict[str, Any]):
    """Print detailed upload summary."""
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    
    if results.get('dry_run'):
        print("🔍 DRY RUN - No actual changes were made")
        print()
    
    print(f"Total courses processed: {results['total_courses']}")
    print(f"Courses matched & updated: {results['courses_updated']}")
    print(f"Course-requirement links: {results['requirements_linked']}")
    print(f"Unique requirements: {results['requirements_found']}")
    
    if results['courses_missing']:
        print(f"\n⚠️  Courses not found in database: {len(results['courses_missing'])}")
        print("   Sample missing courses:")
        for course in results['courses_missing'][:5]:
            print(f"     • {course}")
        if len(results['courses_missing']) > 5:
            print(f"     ... and {len(results['courses_missing']) - 5} more")
    
    
    if results['errors']:
        print(f"\n❌ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"   • {error}")
    
    success_rate = (results['courses_updated'] / results['total_courses']) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")


def main():
    """Main upload function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload course catalog data to database")
    parser.add_argument('json_file', help='Path to catalog JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    
    args = parser.parse_args()
    
    print("📚 Course Catalog Uploader")
    print("=" * 40)
    
    # Load data
    catalog_data = load_catalog_data(args.json_file)
    
    # Upload data
    try:
        results = upload_catalog_data(catalog_data, dry_run=args.dry_run)
        print_upload_summary(results)
        
        if results['errors']:
            print("\n⚠️  Upload completed with errors")
        else:
            print("\n🎉 Upload completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Upload failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()