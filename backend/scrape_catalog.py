#!/usr/bin/env python3
"""
Northwestern Course Catalog Scraper

This script scrapes course information from the Northwestern undergraduate catalog
and saves it to JSON format for database ingestion.

Usage:
    python scrape_catalog.py [options]

Options:
    --limit DEPT_COUNT    Limit number of departments to scrape (for testing)
    --filter DEPT_NAMES   Comma-separated list of department names to scrape only
    --output OUTPUT_DIR   Output directory for results (default: scraped_data)
    --delay SECONDS       Delay between requests (default: 0.5)
    --workers COUNT       Number of parallel workers (default: 3)
    --verbose            Enable verbose logging

Examples:
    # Scrape all departments (full run)
    python scrape_catalog.py
    
    # Test run with first 3 departments
    python scrape_catalog.py --limit 3
    
    # Scrape only Computer Science and Mathematics
    python scrape_catalog.py --filter "Computer Science,Mathematics"
    
    # Faster scraping (be respectful!)
    python scrape_catalog.py --delay 0.2 --workers 5
"""

import argparse
import sys
import time
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from ingestion.catalog import CatalogScraper


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape Northwestern course catalog to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Examples:')[1] if 'Examples:' in __doc__ else ''
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of departments to scrape (for testing)'
    )
    
    parser.add_argument(
        '--filter',
        type=str,
        help='Comma-separated list of department names to scrape only'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='scraped_data',
        help='Output directory for results (default: scraped_data)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of parallel workers (default: 3)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main scraping function."""
    args = parse_args()
    
    # Parse department filter
    department_filter = None
    if args.filter:
        department_filter = [name.strip() for name in args.filter.split(',')]
        print(f"Filtering to departments: {department_filter}")
    
    # Setup scraper
    scraper = CatalogScraper(
        delay_seconds=args.delay,
        max_workers=args.workers,
        output_dir=args.output
    )
    
    print("🎓 Northwestern Course Catalog Scraper")
    print("=" * 50)
    print(f"Output directory: {args.output}")
    print(f"Request delay: {args.delay}s")
    print(f"Parallel workers: {args.workers}")
    
    if args.limit:
        print(f"Limiting to {args.limit} departments")
    if department_filter:
        print(f"Filtering to: {', '.join(department_filter)}")
    
    print("\nStarting scrape...")
    start_time = time.time()
    
    try:
        # Run the scraper
        scraped_data = scraper.scrape_all(
            limit_departments=args.limit,
            department_filter=department_filter
        )
        
        # Save to JSON
        output_file = scraper.save_to_json()
        
        # Print results
        elapsed = time.time() - start_time
        stats = scraper.get_stats()
        
        print("\n✅ Scraping completed successfully!")
        print("=" * 50)
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Departments found: {stats['departments_count']}")
        print(f"Courses found: {stats['courses_count']}")
        print(f"Departments with courses: {stats['departments_with_courses']}")
        print(f"Output saved to: {output_file}")
        
        if stats['sample_courses']:
            print(f"\nSample courses:")
            for course in stats['sample_courses']:
                print(f"  - {course}")
        
        print(f"\n📊 Full data available in: {output_file}")
        print(f"📋 Logs available in: {Path(args.output) / 'scraper.log'}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        print("Partial results may be available in the output directory.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {str(e)}")
        print("Check the log file for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()