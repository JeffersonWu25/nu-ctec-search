#!/usr/bin/env python3
"""
Scrape catalog job - scrape Northwestern course catalog.

Usage:
    python -m app.jobs.scrape_catalog [--departments COMP_SCI,MATH] [--limit 5]
"""

import sys
import argparse

from ..services.catalog_service import scrape_and_upload_catalog
from ..utils.logging import get_job_logger


def print_detailed_summary(results):
    """Print detailed department and update validation summary."""
    print("\n" + "=" * 60)
    print("📊 SCRAPING & UPDATE SUMMARY")
    print("=" * 60)
    
    # Department scraping results
    dept_results = results.get('department_results', {})
    total_depts = dept_results.get('total_departments', 0)
    successful_depts = dept_results.get('successful_count', 0) 
    failed_depts = dept_results.get('failed_count', 0)
    no_courses_depts = dept_results.get('departments_with_no_courses', [])
    
    print(f"📚 Department Scraping:")
    print(f"   ✅ Successful: {successful_depts}/{total_depts}")
    if failed_depts > 0:
        print(f"   ❌ Failed: {failed_depts}")
        failed_list = dept_results.get('failed_departments', [])
        for dept_name, error in failed_list[:5]:  # Show first 5
            print(f"      • {dept_name}: {error[:50]}...")
        if len(failed_list) > 5:
            print(f"      ... and {len(failed_list) - 5} more")
    
    if no_courses_depts:
        print(f"   ⚠️  Departments with no courses: {len(no_courses_depts)}")
        for dept_name, count in no_courses_depts[:5]:
            print(f"      • {dept_name}")
        if len(no_courses_depts) > 5:
            print(f"      ... and {len(no_courses_depts) - 5} more")
    
    # Course update results
    print(f"\n📝 Database Updates:")
    total_courses = results.get('total_courses', 0)
    matched_courses = results.get('courses_matched', 0)
    updated_courses = results.get('courses_updated', 0)
    missing_courses = results.get('courses_missing', [])
    
    print(f"   📚 Courses from catalog: {total_courses}")
    print(f"   ✅ Found in database: {matched_courses}")
    print(f"   📝 Updated successfully: {updated_courses}")
    if len(missing_courses) > 0:
        print(f"   ❌ Missing from database: {len(missing_courses)} (skipped)")
    
    # Requirements results
    req_found = results.get('requirements_found', 0)
    req_linked = results.get('requirements_linked', 0)
    
    if req_found > 0:
        print(f"   📋 Requirements processed: {req_found}")
        print(f"   🔗 Course-requirement links: {req_linked}")
    
    # Error summary
    errors = results.get('errors', [])
    if errors:
        print(f"\n⚠️  Errors encountered: {len(errors)}")
        for error in errors[:3]:  # Show first 3
            print(f"   • {error}")
        if len(errors) > 3:
            print(f"   ... and {len(errors) - 3} more")
    
    print("=" * 60)


def main():
    """Main entry point for scrape catalog job."""
    parser = argparse.ArgumentParser(
        description="Scrape Northwestern course catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.scrape_catalog                              # Scrape all departments
  python -m app.jobs.scrape_catalog --limit 5                   # Scrape first 5 departments
  python -m app.jobs.scrape_catalog --departments COMP_SCI,MATH # Scrape specific departments
  python -m app.jobs.scrape_catalog --save-only                 # Scrape and save, don't upload
  python -m app.jobs.scrape_catalog --empty-only                # Only update courses with empty catalog data
        """
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
    parser.add_argument(
        '--save-only',
        action='store_true',
        help='Save scraped data but do not upload to database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview upload changes without applying (implies upload)'
    )
    parser.add_argument(
        '--empty-only',
        action='store_true',
        help='Only update courses with completely empty catalog data (no description, prerequisites, or requirements)'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('scrape_catalog')
    logger.info("📚 Northwestern Catalog Scraper")
    logger.info("=" * 40)
    
    try:
        department_filter = None
        if args.departments:
            department_filter = [dept.strip() for dept in args.departments.split(',')]
            logger.info(f"Filtering to departments: {department_filter}")
        
        if args.limit:
            logger.info(f"Limiting to {args.limit} departments")
        
        # Run scrape and upload workflow
        results = scrape_and_upload_catalog(
            dry_run=args.dry_run,
            department_filter=department_filter,
            limit_departments=args.limit,
            empty_courses_only=args.empty_only
        )
        
        if 'error' in results:
            print(f"❌ Scraping failed: {results['error']}")
            sys.exit(1)
        elif results.get('cancelled'):
            print("❌ Upload cancelled by user")
            if 'backup_file' in results:
                print(f"📄 Scraped data saved to: {results['backup_file']}")
            return
        else:
            # Print detailed validation results
            print_detailed_summary(results)
            
            if not args.save_only:
                courses_updated = results.get('courses_updated', 0)
                courses_matched = results.get('courses_matched', 0)
                print(f"\n🎉 Scraping completed successfully!")
                if 'backup_file' in results:
                    print(f"📄 Data saved to: {results['backup_file']}")
                print(f"📚 Updated {courses_updated}/{courses_matched} courses in database")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()