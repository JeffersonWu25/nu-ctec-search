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
            limit_departments=args.limit
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
            print(f"\n🎉 Scraping completed successfully!")
            if 'backup_file' in results:
                print(f"📄 Data saved to: {results['backup_file']}")
            
            if not args.save_only:
                courses_updated = results.get('courses_updated', 0)
                courses_matched = results.get('courses_matched', 0)
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