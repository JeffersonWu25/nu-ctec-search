#!/usr/bin/env python3
"""
Upload departments job - thin wrapper around department service.

Usage:
    python -m app.jobs.upload_departments [json_file] [--dry-run]
"""

import sys
import argparse
from pathlib import Path

from ..services.department_service import (
    upload_departments_data,
    load_departments_from_file,
    scrape_and_upload_departments
)
from ..utils.logging import get_job_logger
from ..settings import settings


def print_summary(results: dict):
    """Print upload summary."""
    print("\n" + "=" * 50)
    print("📊 UPLOAD SUMMARY")
    print("=" * 50)
    print(f"Total departments: {results.get('total', 0)}")
    print(f"Successfully uploaded: {results.get('uploaded', 0)}")
    print(f"Errors: {len(results.get('errors', []))}")
    
    if results.get('errors'):
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results.get('total', 0) > 0:
        success_rate = (results.get('uploaded', 0) / results['total']) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")


def main():
    """Main entry point for upload departments job."""
    parser = argparse.ArgumentParser(
        description="Upload departments to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.upload_departments                           # Use default departments file
  python -m app.jobs.upload_departments custom.json              # Use custom file
  python -m app.jobs.upload_departments --scrape                 # Scrape then upload
  python -m app.jobs.upload_departments --dry-run                # Preview changes
        """
    )
    
    parser.add_argument(
        'json_file', 
        nargs='?',
        help='Path to departments JSON file (default: scraped_data/departments_mapping.json)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview changes without applying'
    )
    parser.add_argument(
        '--scrape',
        action='store_true', 
        help='Scrape departments first, then upload'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('upload_departments')
    logger.info("🏫 Department Uploader")
    logger.info("=" * 30)
    
    try:
        if args.scrape:
            # Scrape and upload workflow
            logger.info("Running scrape and upload workflow")
            results = scrape_and_upload_departments(dry_run=args.dry_run)
            
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
                if results.get('uploaded', 0) == results.get('total', 0):
                    print("\n🎉 All departments uploaded successfully!")
                else:
                    print(f"\n⚠️  {results.get('total', 0) - results.get('uploaded', 0)} departments failed")
        else:
            # File upload workflow
            if args.json_file:
                departments_file = Path(args.json_file)
            else:
                departments_file = settings.SCRAPED_DATA_DIR / "departments_mapping.json"
            
            logger.info(f"Loading departments from: {departments_file}")
            
            # Load and validate departments data
            departments_data = load_departments_from_file(departments_file)
            
            # Show sample data
            print(f"\nSample departments:")
            for i, dept in enumerate(departments_data[:5], 1):
                print(f"  {i}. {dept['name']} ({dept['code']})")
            
            if len(departments_data) > 5:
                print(f"  ... and {len(departments_data) - 5} more")
            
            # Upload departments
            results = upload_departments_data(departments_data, dry_run=args.dry_run)
            
            if 'error' in results:
                print(f"❌ Upload failed: {results['error']}")
                sys.exit(1)
            
            print_summary(results)
            
            if results.get('uploaded', 0) == results.get('total', 0):
                print("\n🎉 All departments uploaded successfully!")
            else:
                print(f"\n⚠️  {results.get('total', 0) - results.get('uploaded', 0)} departments failed")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()