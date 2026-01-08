#!/usr/bin/env python3
"""
Scrape departments job - scrape Northwestern departments.

Usage:
    python -m app.jobs.scrape_departments [--save-only]
"""

import sys
import argparse

from ..services.department_service import scrape_and_upload_departments
from ..utils.logging import get_job_logger


def main():
    """Main entry point for scrape departments job."""
    parser = argparse.ArgumentParser(
        description="Scrape Northwestern departments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.scrape_departments                          # Scrape and upload
  python -m app.jobs.scrape_departments --save-only             # Scrape and save, don't upload
  python -m app.jobs.scrape_departments --dry-run               # Preview upload changes
        """
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
    
    logger = get_job_logger('scrape_departments')
    logger.info("🏫 Northwestern Departments Scraper")
    logger.info("=" * 40)
    
    try:
        # Run scrape and upload workflow
        results = scrape_and_upload_departments(dry_run=args.dry_run)
        
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
                uploaded = results.get('uploaded', 0)
                total = results.get('total', 0)
                print(f"🏫 Uploaded {uploaded}/{total} departments to database")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()