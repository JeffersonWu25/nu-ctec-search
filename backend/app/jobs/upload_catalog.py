#!/usr/bin/env python3
"""
Upload catalog job - thin wrapper around catalog service.

Usage:
    python -m app.jobs.upload_catalog [json_file] [--dry-run]
"""

import sys
import argparse
from pathlib import Path

from ..services.catalog_service import (
    update_course_catalog_data,
    load_catalog_from_file,
    scrape_and_upload_catalog
)
from ..utils.logging import get_job_logger
from ..settings import settings


def print_summary(results: dict):
    """Print upload summary."""
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    
    if results.get('dry_run'):
        print("🔍 DRY RUN - No actual changes were made")
        print()
    
    print(f"Total courses processed: {results.get('total_courses', 0)}")
    print(f"Courses matched & updated: {results.get('courses_updated', 0)}")
    print(f"Course-requirement links: {results.get('requirements_linked', 0)}")
    print(f"Unique requirements: {results.get('requirements_found', 0)}")
    
    missing_courses = results.get('courses_missing', [])
    if missing_courses:
        print(f"\n⚠️  Courses not found in database: {len(missing_courses)}")
        print("   Sample missing courses:")
        for course in missing_courses[:5]:
            print(f"     • {course}")
        if len(missing_courses) > 5:
            print(f"     ... and {len(missing_courses) - 5} more")
    
    errors = results.get('errors', [])
    if errors:
        print(f"\n❌ Errors: {len(errors)}")
        for error in errors:
            print(f"   • {error}")
    
    if results.get('total_courses', 0) > 0:
        success_rate = (results.get('courses_updated', 0) / results['total_courses']) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")


def main():
    """Main entry point for upload catalog job."""
    parser = argparse.ArgumentParser(
        description="Upload course catalog data to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.upload_catalog                               # Use default catalog file
  python -m app.jobs.upload_catalog custom.json                  # Use custom file
  python -m app.jobs.upload_catalog --scrape                     # Scrape then upload
  python -m app.jobs.upload_catalog --dry-run                    # Preview changes
  python -m app.jobs.upload_catalog --scrape --departments COMP_SCI,MATH  # Scrape specific departments
        """
    )
    
    parser.add_argument(
        'json_file',
        nargs='?',
        help='Path to catalog JSON file (default: scraped_data/catalog_data.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying'
    )
    parser.add_argument(
        '--scrape',
        action='store_true',
        help='Scrape catalog first, then upload'
    )
    parser.add_argument(
        '--departments',
        help='Comma-separated list of department codes to scrape (e.g., COMP_SCI,MATH)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of departments to scrape'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('upload_catalog')
    logger.info("📚 Course Catalog Uploader")
    logger.info("=" * 40)
    
    try:
        if args.scrape:
            # Scrape and upload workflow
            logger.info("Running scrape and upload workflow")
            
            department_filter = None
            if args.departments:
                department_filter = [dept.strip() for dept in args.departments.split(',')]
                logger.info(f"Filtering to departments: {department_filter}")
            
            results = scrape_and_upload_catalog(
                dry_run=args.dry_run,
                department_filter=department_filter,
                limit_departments=args.limit
            )
            
            if 'error' in results:
                print(f"❌ Workflow failed: {results['error']}")
                sys.exit(1)
            elif results.get('cancelled'):
                print("❌ Upload cancelled by user")
                if 'backup_file' in results:
                    print(f"📄 Scraped data saved to: {results['backup_file']}")
                return
            else:
                print_summary(results)
                if results.get('errors'):
                    print("\n⚠️  Upload completed with errors")
                else:
                    print("\n🎉 Upload completed successfully!")
        else:
            # File upload workflow
            if args.json_file:
                catalog_file = Path(args.json_file)
            else:
                catalog_file = settings.SCRAPED_DATA_DIR / "catalog_data.json"
            
            logger.info(f"Loading catalog from: {catalog_file}")
            
            # Load catalog data
            catalog_data = load_catalog_from_file(catalog_file)
            
            # Upload catalog data
            results = update_course_catalog_data(catalog_data, dry_run=args.dry_run)
            
            if 'error' in results:
                print(f"❌ Upload failed: {results['error']}")
                sys.exit(1)
            
            print_summary(results)
            
            if results.get('errors'):
                print("\n⚠️  Upload completed with errors")
            else:
                print("\n🎉 Upload completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()