#!/usr/bin/env python3
"""
Update department_id column in courses table.

This script extracts department codes from course codes and populates
the department_id field by matching with the departments table.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from api.supabase_client import supabase


def extract_department_code(course_code: str) -> Optional[str]:
    """
    Extract department code from course code.
    
    Examples:
        'AFST_101-7' -> 'AFST'
        'AMER_ST_276-0' -> 'AMER_ST'
        'COMP_SCI_150-0' -> 'COMP_SCI'
        'ECON_201' -> 'ECON'
    
    Args:
        course_code: Full course code from database
        
    Returns:
        Department code or None if unable to extract
    """
    if not course_code:
        return None
    
    # Split on underscore
    parts = course_code.split('_')
    
    if len(parts) < 2:
        return None
    
    # Find the first part that contains a number
    dept_parts = []
    for part in parts:
        # If this part starts with a number, we've found the course number
        if re.match(r'^\d', part):
            break
        dept_parts.append(part)
    
    if not dept_parts:
        return None
    
    # Join department parts back with underscore
    return '_'.join(dept_parts)


def get_courses_without_department_id() -> List[Dict]:
    """Get all courses that don't have a department_id set."""
    print("🔍 Fetching courses without department_id...")
    
    try:
        response = supabase.table('courses').select('id, code').is_('department_id', 'null').execute()
        courses = response.data
        
        print(f"   Found {len(courses)} courses without department_id")
        return courses
        
    except Exception as e:
        print(f"❌ Error fetching courses: {str(e)}")
        return []


def build_department_lookup() -> Dict[str, str]:
    """Build lookup map from department code to department ID."""
    print("🗃️  Building department lookup map...")
    
    try:
        response = supabase.table('departments').select('id, code').execute()
        departments = response.data
        
        lookup_map = {dept['code']: dept['id'] for dept in departments}
        
        print(f"   Found {len(lookup_map)} departments")
        return lookup_map
        
    except Exception as e:
        print(f"❌ Error fetching departments: {str(e)}")
        return {}


def update_courses_with_departments(courses: List[Dict], dept_lookup: Dict[str, str], dry_run: bool = False) -> Dict:
    """Update courses with department_id based on extracted department codes."""
    print("🔄 Processing course department assignments...")
    
    results = {
        'total_courses': len(courses),
        'matched': 0,
        'updated': 0,
        'no_match': 0,
        'extraction_failed': 0,
        'errors': []
    }
    
    if dry_run:
        print("   🔍 DRY RUN MODE - No changes will be made")
    
    for course in courses:
        course_id = course['id']
        course_code = course['code']
        
        # Extract department code
        dept_code = extract_department_code(course_code)
        
        if not dept_code:
            results['extraction_failed'] += 1
            print(f"   ⚠️  Failed to extract department from: {course_code}")
            continue
        
        # Look up department ID
        if dept_code not in dept_lookup:
            results['no_match'] += 1
            print(f"   ❌ No department found for code: {dept_code} (from {course_code})")
            continue
        
        dept_id = dept_lookup[dept_code]
        results['matched'] += 1
        
        if not dry_run:
            # Update the course
            try:
                supabase.table('courses').update({'department_id': dept_id}).eq('id', course_id).execute()
                results['updated'] += 1
                print(f"   ✅ Updated {course_code} -> {dept_code} (ID: {dept_id})")
                
            except Exception as e:
                error_msg = f"Failed to update course {course_code}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
        else:
            print(f"   [DRY RUN] Would update {course_code} -> {dept_code} (ID: {dept_id})")
            results['updated'] += 1
    
    return results


def print_summary(results: Dict, dry_run: bool = False):
    """Print detailed summary of the update operation."""
    print("\n" + "=" * 60)
    print("📊 UPDATE SUMMARY")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN - No actual changes were made")
        print()
    
    print(f"Total courses processed: {results['total_courses']}")
    print(f"Department codes extracted: {results['matched'] + results['no_match']}")
    print(f"Courses matched & updated: {results['updated']}")
    print(f"Courses with no matching department: {results['no_match']}")
    print(f"Extraction failures: {results['extraction_failed']}")
    
    if results['errors']:
        print(f"\n❌ Update errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"   • {error}")
    
    if results['total_courses'] > 0:
        success_rate = (results['updated'] / results['total_courses']) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")
    
    print()


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update department_id for courses")
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--sample', type=int, help='Process only first N courses (for testing)')
    
    args = parser.parse_args()
    
    print("🏫 Course Department ID Updater")
    print("=" * 40)
    
    try:
        # Get courses without department_id
        courses = get_courses_without_department_id()
        
        if not courses:
            print("✅ All courses already have department_id assigned!")
            return
        
        # Limit to sample if specified
        if args.sample:
            courses = courses[:args.sample]
            print(f"📝 Processing sample of {len(courses)} courses")
        
        # Build department lookup
        dept_lookup = build_department_lookup()
        
        if not dept_lookup:
            print("❌ No departments found in database. Please upload departments first.")
            sys.exit(1)
        
        # Show sample of what will be processed
        print(f"\n📋 Sample courses to process:")
        for i, course in enumerate(courses[:5], 1):
            dept_code = extract_department_code(course['code'])
            match_status = "✅" if dept_code and dept_code in dept_lookup else "❌"
            print(f"  {i}. {course['code']} -> {dept_code} {match_status}")
        
        if len(courses) > 5:
            print(f"     ... and {len(courses) - 5} more")
        
        # Confirm update
        if not args.dry_run:
            confirm = input(f"\nProceed with updating {len(courses)} courses? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Update cancelled by user.")
                return
        
        # Update courses
        results = update_courses_with_departments(courses, dept_lookup, dry_run=args.dry_run)
        
        # Print summary
        print_summary(results, dry_run=args.dry_run)
        
        if results['errors']:
            print("⚠️  Update completed with errors")
        elif results['updated'] == results['total_courses']:
            print("🎉 All courses updated successfully!")
        else:
            print("✅ Update completed")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Update failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()