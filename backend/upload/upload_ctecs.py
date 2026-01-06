"""
Main entry point for the CTEC upload system.
Provides both terminal interface and command-line options.
"""

import sys
import argparse
from pathlib import Path


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="CTEC Upload System - Parse and upload CTEC PDFs to database",
        epilog="Examples:\n"
               "  python upload_ctecs.py                    # Interactive terminal interface\n"
               "  python upload_ctecs.py --file doc.pdf     # Upload single file\n"
               "  python upload_ctecs.py --all              # Upload all files in docs/upload\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--file", type=str, help="Upload a single PDF file")
    parser.add_argument("--all", action="store_true", help="Upload all files in docs/upload")
    parser.add_argument("--upload-dir", type=str, help="Custom upload directory (default: docs/upload)")
    parser.add_argument("--no-interface", action="store_true", help="Skip terminal interface for batch operations")
    
    args = parser.parse_args()
    
    # If no arguments provided, run interactive interface
    if not any([args.file, args.all]):
        from terminal_interface import TerminalInterface
        interface = TerminalInterface()
        interface.run()
        return
    
    # Handle command-line operations
    from upload_pipeline import UploadPipeline
    pipeline = UploadPipeline()
    
    if args.file:
        # Single file upload
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            print(f"❌ Error: File not found: {pdf_path}")
            sys.exit(1)
        
        print(f"🚀 Uploading single file: {pdf_path.name}")
        success = pipeline.process_single_file(pdf_path)
        sys.exit(0 if success else 1)
    
    elif args.all:
        # Batch upload
        upload_dir = Path(args.upload_dir) if args.upload_dir else Path("docs/upload")
        
        if not upload_dir.exists():
            print(f"❌ Error: Upload directory not found: {upload_dir}")
            sys.exit(1)
        
        print(f"🚀 Batch uploading from: {upload_dir}")
        stats = pipeline.process_all_files(upload_dir)
        
        print("\n" + "=" * 60)
        print("📊 BATCH UPLOAD COMPLETE")
        print("=" * 60)
        print(f"Total files: {stats['total_files']}")
        print(f"Successfully uploaded: {stats['successful_uploads']}")
        print(f"Parse failures: {stats['parse_failures']}")
        print(f"Upload failures: {stats['upload_failures']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Total time: {stats['total_time']}")
        
        sys.exit(0 if stats['successful_uploads'] > 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)