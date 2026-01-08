#!/usr/bin/env python3
"""
Update course departments job - thin wrapper around department service.

Usage:
    python -m app.jobs.update_course_departments [--dry-run] [--sample N]
"""

import sys
import argparse

from ..services.department_service import update_course_department_mappings
from ..utils.logging import get_job_logger


def print_summary(results: dict, dry_run: bool = False):
    """Print detailed summary of the update operation."""
    print("\n" + "=" * 60)
    print("📊 UPDATE SUMMARY")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN - No actual changes were made")
        print()
    
    print(f"Total courses processed: {results.get('total_courses', 0)}")
    print(f"Department codes extracted: {results.get('matched', 0) + results.get('no_match', 0)}")
    print(f"Courses matched & updated: {results.get('updated', 0)}")
    print(f"Courses with no matching department: {results.get('no_match', 0)}")
    print(f"Extraction failures: {results.get('extraction_failed', 0)}")
    
    errors = results.get('errors', [])
    if errors:
        print(f"\n❌ Update errors: {len(errors)}")
        for error in errors:
            print(f"   • {error}")
    
    if results.get('total_courses', 0) > 0:
        success_rate = (results.get('updated', 0) / results['total_courses']) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")
    
    print()


def main():
    """Main entry point for update course departments job."""
    parser = argparse.ArgumentParser(
        description="Update department_id for courses by extracting department codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.update_course_departments                    # Update all courses
  python -m app.jobs.update_course_departments --dry-run         # Preview changes
  python -m app.jobs.update_course_departments --sample 10       # Test on 10 courses
  python -m app.jobs.update_course_departments --sample 10 --dry-run  # Preview sample
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Process only first N courses (for testing)'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('update_course_departments')
    logger.info("🏫 Course Department ID Updater")
    logger.info("=" * 40)
    
    try:
        # Run the update
        results = update_course_department_mappings(
            dry_run=args.dry_run,
            sample_size=args.sample
        )
        
        if 'error' in results:
            print(f"❌ Update failed: {results['error']}")
            sys.exit(1)
        
        if results.get('total_courses', 0) == 0:
            print("✅ All courses already have department_id assigned!")
            return
        
        # Show sample of what was processed
        if args.sample:
            print(f"\n📝 Processing sample of {args.sample} courses")
        
        # Print results
        print_summary(results, dry_run=args.dry_run)
        
        if results.get('errors'):
            print("⚠️  Update completed with errors")
        elif results.get('updated', 0) == results.get('total_courses', 0):
            print("🎉 All courses updated successfully!")
        else:
            print("✅ Update completed")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()