#!/usr/bin/env python3
"""
Upload CTECs job - thin wrapper around CTEC service.

Usage:
    python -m app.jobs.upload_ctecs [--file path.pdf] [--all] [--upload-dir path]
"""

import sys
import argparse
import json
from pathlib import Path

from ..services.ctec_service import parse_and_upload_ctec, process_ctec_batch
from ..parsing.ctec.ctec_parser import ParserConfig, CTECParser
from ..utils.logging import get_job_logger
from ..settings import settings


def print_batch_summary(results: dict):
    """Print batch upload summary."""
    print("\n" + "=" * 60)
    print("📊 BATCH UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Total files: {results.get('total_files', 0)}")
    print(f"Successfully uploaded: {results.get('successful_uploads', 0)}")
    print(f"Parse failures: {results.get('parse_failures', 0)}")
    print(f"Upload failures: {results.get('upload_failures', 0)}")
    print(f"Success rate: {results.get('success_rate', 0):.1f}%")
    print(f"Total time: {results.get('total_time', 'Unknown')}")
    
    errors = results.get('errors', [])
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   • {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")


def print_single_file_summary(result: dict, verbose: bool = False):
    """Print single file upload summary."""
    print("\n" + "=" * 50)
    print("📊 UPLOAD RESULT")
    print("=" * 50)
    
    if result['status'] == 'success':
        course_info = result['course_info']
        upload_results = result['upload_results']
        
        print(f"File: {result['file']}")
        print(f"Course: {course_info['code']} - {course_info['title']}")
        print(f"Instructor: {course_info['instructor']}")
        print(f"Term: {course_info['quarter']} {course_info['year']}")
        print(f"Section: {course_info.get('section', 'N/A')}")
        
        if upload_results.get('uploaded'):
            print(f"Comments uploaded: {upload_results.get('comments_uploaded', 0)}")
            print(f"Ratings uploaded: {upload_results.get('ratings_uploaded', 0)}")
            print("\n🎉 Upload successful!")
        else:
            print(f"\n❌ Upload failed: {upload_results.get('error', 'Unknown error')}")
            
        # Show detailed JSON data if verbose mode is enabled
        if verbose and 'parsed_data' in result:
            print("\n" + "=" * 50)
            print("📋 DETAILED PARSED DATA")
            print("=" * 50)
            print(json.dumps(result['parsed_data'], indent=2, ensure_ascii=False))
    else:
        print(f"File: {result['file']}")
        print(f"❌ Parse failed: {result.get('error', 'Unknown error')}")


def main():
    """Main entry point for upload CTECs job."""
    parser = argparse.ArgumentParser(
        description="CTEC Upload System - Parse and upload CTEC PDFs to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.upload_ctecs --file doc.pdf                    # Upload single file
  python -m app.jobs.upload_ctecs --file doc.pdf --dry-run          # Preview single file
  python -m app.jobs.upload_ctecs --file doc.pdf --dry-run --verbose # Show detailed parsed data
  python -m app.jobs.upload_ctecs --all                             # Upload all files in docs/upload
  python -m app.jobs.upload_ctecs --all --upload-dir /custom/dir    # Use custom directory
  python -m app.jobs.upload_ctecs --file doc.pdf --debug            # Enable debug mode
        """
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Upload a single PDF file'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Upload all files in upload directory'
    )
    parser.add_argument(
        '--upload-dir',
        type=str,
        help='Custom upload directory (default: docs/upload)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode for parser'
    )
    parser.add_argument(
        '--continue-on-errors',
        action='store_true',
        help='Continue processing even if OCR validation fails'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed parsed data in JSON format'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('upload_ctecs')
    logger.info("📋 CTEC Upload System")
    logger.info("=" * 30)
    
    # Configure parser
    parser_config = ParserConfig(
        debug=args.debug,
        validate_ocr_totals=not args.continue_on_errors,
        continue_on_ocr_errors=args.continue_on_errors,
        extract_comments=True,
        extract_demographics=True,
        extract_time_survey=True
    )
    
    try:
        if args.file:
            # Single file upload
            pdf_path = Path(args.file)
            if not pdf_path.exists():
                print(f"❌ Error: File not found: {pdf_path}")
                sys.exit(1)
            
            print(f"🚀 Uploading single file: {pdf_path.name}")
            
            # If verbose mode, parse the data separately to include in output
            if args.verbose:
                try:
                    parser = CTECParser(parser_config)
                    ctec_data = parser.parse_ctec(str(pdf_path))
                    parsed_data_dict = ctec_data.to_dict()
                except Exception as e:
                    parsed_data_dict = {"error": f"Failed to parse for verbose output: {e}"}
            
            result = parse_and_upload_ctec(pdf_path, dry_run=args.dry_run, parser_config=parser_config)
            
            # Add parsed data to result for verbose output
            if args.verbose:
                result['parsed_data'] = parsed_data_dict
            
            print_single_file_summary(result, verbose=args.verbose)
            
            if result['status'] == 'success' and result['upload_results'].get('uploaded'):
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.all:
            # Batch upload
            if args.upload_dir:
                upload_dir = Path(args.upload_dir)
            else:
                upload_dir = Path("docs/upload")
            
            if not upload_dir.exists():
                print(f"❌ Error: Upload directory not found: {upload_dir}")
                sys.exit(1)
            
            print(f"🚀 Batch uploading from: {upload_dir}")
            results = process_ctec_batch(upload_dir, dry_run=args.dry_run, parser_config=parser_config)
            
            if 'error' in results:
                print(f"❌ Error: {results['error']}")
                sys.exit(1)
            elif results.get('cancelled'):
                print("❌ Upload cancelled by user")
                return
            
            print_batch_summary(results)
            
            if results.get('successful_uploads', 0) > 0:
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            # No arguments provided - show help
            parser.print_help()
            print("\n💡 Tip: Use --file for single files or --all for batch processing")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()