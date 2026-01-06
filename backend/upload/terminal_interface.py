"""
Interactive terminal interface for CTEC upload system.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from pdf_processor import PDFProcessor


class TerminalInterface:
    def __init__(self):
        """Initialize the terminal interface."""
        self.processor = PDFProcessor()
        self.upload_dir = self._get_upload_directory()
    
    def _get_upload_directory(self) -> Path:
        """Get the upload directory path."""
        script_dir = Path(__file__).parent
        upload_dir = script_dir.parent.parent / "docs" / "upload"
        
        # Create upload directory if it doesn't exist
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the application header."""
        print("=" * 60)
        print("🎓 NORTHWESTERN CTEC UPLOAD SYSTEM")
        print("=" * 60)
        print(f"Upload Directory: {self.upload_dir}")
        print()
    
    def get_pdf_files(self) -> List[Path]:
        """Get list of PDF files in the upload directory."""
        try:
            return self.processor.get_upload_directory_files(self.upload_dir)
        except FileNotFoundError:
            return []
    
    def display_main_menu(self) -> str:
        """Display main menu and get user choice."""
        pdf_files = self.get_pdf_files()
        
        print("📋 MAIN MENU")
        print("-" * 20)
        print("1. Upload single file")
        print("2. Upload all files")
        print("3. View files in upload directory")
        print("4. Exit")
        print()
        
        if pdf_files:
            print(f"📁 {len(pdf_files)} PDF files found in upload directory")
        else:
            print("⚠️  No PDF files found in upload directory")
            print(f"   Please add PDF files to: {self.upload_dir}")
        
        print()
        choice = input("Select option (1-4): ").strip()
        return choice
    
    def display_file_selection(self, pdf_files: List[Path]) -> Optional[Path]:
        """Display file selection menu."""
        if not pdf_files:
            print("❌ No PDF files available for selection")
            input("Press Enter to continue...")
            return None
        
        print("📁 SELECT FILE TO UPLOAD")
        print("-" * 30)
        
        for i, pdf_file in enumerate(pdf_files, 1):
            file_size = pdf_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"{i:2}. {pdf_file.name} ({size_mb:.1f} MB)")
        
        print(f"{len(pdf_files) + 1:2}. Back to main menu")
        print()
        
        try:
            choice = input(f"Select file (1-{len(pdf_files) + 1}): ").strip()
            choice_num = int(choice)
            
            if choice_num == len(pdf_files) + 1:
                return None
            
            if 1 <= choice_num <= len(pdf_files):
                return pdf_files[choice_num - 1]
            else:
                print("❌ Invalid selection")
                input("Press Enter to continue...")
                return None
                
        except ValueError:
            print("❌ Please enter a valid number")
            input("Press Enter to continue...")
            return None
    
    def display_files_list(self, pdf_files: List[Path]):
        """Display list of files in upload directory."""
        self.clear_screen()
        self.print_header()
        
        if not pdf_files:
            print("📁 UPLOAD DIRECTORY CONTENTS")
            print("-" * 30)
            print("No PDF files found")
            print(f"\nTo add files, copy PDFs to: {self.upload_dir}")
        else:
            print("📁 UPLOAD DIRECTORY CONTENTS")
            print("-" * 30)
            total_size = 0
            
            for i, pdf_file in enumerate(pdf_files, 1):
                file_size = pdf_file.stat().st_size
                size_mb = file_size / (1024 * 1024)
                total_size += file_size
                print(f"{i:2}. {pdf_file.name} ({size_mb:.1f} MB)")
            
            total_mb = total_size / (1024 * 1024)
            print(f"\nTotal: {len(pdf_files)} files ({total_mb:.1f} MB)")
        
        print()
        input("Press Enter to continue...")
    
    def confirm_upload(self, message: str) -> bool:
        """Get confirmation from user for upload operation."""
        print()
        print("⚠️  UPLOAD CONFIRMATION")
        print("-" * 25)
        print(message)
        print()
        
        while True:
            choice = input("Continue? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def show_upload_progress(self, current: int, total: int, filename: str, status: str):
        """Show upload progress for current file."""
        progress_bar_width = 40
        progress = current / total
        filled = int(progress_bar_width * progress)
        bar = "█" * filled + "░" * (progress_bar_width - filled)
        
        print(f"\r[{current:3}/{total}] [{bar}] {progress:.1%} | {status}: {filename}", end="", flush=True)
    
    def run_single_file_upload(self) -> bool:
        """Run single file upload workflow."""
        from upload_pipeline import UploadPipeline
        
        pdf_files = self.get_pdf_files()
        selected_file = self.display_file_selection(pdf_files)
        
        if not selected_file:
            return False
        
        self.clear_screen()
        self.print_header()
        
        if not self.confirm_upload(f"Upload file: {selected_file.name}"):
            return False
        
        print(f"\n🚀 Starting upload of: {selected_file.name}")
        print("=" * 60)
        
        pipeline = UploadPipeline()
        success = pipeline.process_single_file(selected_file)
        
        print("\n" + "=" * 60)
        if success:
            print("✅ Upload completed successfully!")
        else:
            print("❌ Upload failed!")
        
        input("Press Enter to continue...")
        return success
    
    def run_batch_upload(self) -> bool:
        """Run batch upload workflow."""
        from upload_pipeline import UploadPipeline
        
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            print("❌ No files to upload")
            input("Press Enter to continue...")
            return False
        
        self.clear_screen()
        self.print_header()
        
        if not self.confirm_upload(f"Upload all {len(pdf_files)} files from upload directory"):
            return False
        
        print(f"\n🚀 Starting batch upload of {len(pdf_files)} files...")
        print("=" * 60)
        
        pipeline = UploadPipeline()
        stats = pipeline.process_all_files(self.upload_dir)
        
        print("\n" + "=" * 60)
        print("📊 BATCH UPLOAD COMPLETE")
        print("=" * 60)
        print(f"Total files: {stats['total_files']}")
        print(f"Successfully uploaded: {stats['successful_uploads']}")
        print(f"Parse failures: {stats['parse_failures']}")
        print(f"Upload failures: {stats['upload_failures']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Total time: {stats['total_time']}")
        
        input("Press Enter to continue...")
        return stats['successful_uploads'] > 0
    
    def run(self):
        """Run the main terminal interface loop."""
        while True:
            self.clear_screen()
            self.print_header()
            
            choice = self.display_main_menu()
            
            if choice == '1':
                self.run_single_file_upload()
            elif choice == '2':
                self.run_batch_upload()
            elif choice == '3':
                pdf_files = self.get_pdf_files()
                self.display_files_list(pdf_files)
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
                input("Press Enter to continue...")


def main():
    """Main entry point for the terminal interface."""
    try:
        interface = TerminalInterface()
        interface.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()