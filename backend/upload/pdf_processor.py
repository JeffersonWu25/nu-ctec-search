"""
PDF processor for parsing CTEC files and preparing them for upload.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class PDFProcessor:
    def __init__(self):
        """Initialize the PDF processor."""
        self.script_dir = Path(__file__).parent
        self.parser_script = self.script_dir.parent / "parser" / "batch_parse_ctecs.py"
        
        if not self.parser_script.exists():
            raise FileNotFoundError(f"Parser script not found: {self.parser_script}")
    
    def parse_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Parse a single PDF file using the batch parser.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Parsed CTEC data dictionary
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF: {pdf_path}")
        
        try:
            # Call the parser script with JSON output
            cmd = [
                sys.executable,
                str(self.parser_script),
                "--file", str(pdf_path),
                "--json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown parser error"
                return {
                    "status": "error",
                    "file": pdf_path.name,
                    "error": error_msg,
                    "error_type": "ParserError"
                }
            
            # Parse the JSON output
            try:
                parsed_data = json.loads(result.stdout)
                return parsed_data
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "file": pdf_path.name,
                    "error": f"Invalid JSON output from parser: {e}",
                    "error_type": "JSONDecodeError"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "file": pdf_path.name,
                "error": "Parser timeout (5 minutes)",
                "error_type": "TimeoutError"
            }
        except Exception as e:
            return {
                "status": "error",
                "file": pdf_path.name,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def validate_parsed_data(self, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate that parsed data has required fields for upload.
        
        Args:
            parsed_data: Result from parse_single_pdf
            
        Returns:
            True if data is valid for upload
        """
        if parsed_data.get("status") != "success":
            return False
        
        data = parsed_data.get("data", {})
        
        # Check required fields
        required_fields = ["course", "instructor", "course_offering"]
        for field in required_fields:
            if field not in data:
                return False
        
        # Check course
        course = data.get("course", {})
        if not course.get("code") or not course.get("title"):
            return False
        
        # Check instructor
        instructor = data.get("instructor", {})
        if not instructor.get("name"):
            return False
        
        # Check offering
        offering = data.get("course_offering", {})
        if not offering.get("quarter") or not offering.get("year"):
            return False
        
        return True
    
    def get_upload_directory_files(self, upload_dir: Optional[Path] = None) -> list[Path]:
        """
        Get list of PDF files in the upload directory.
        
        Args:
            upload_dir: Custom upload directory, defaults to docs/upload
            
        Returns:
            List of PDF file paths
        """
        if upload_dir is None:
            upload_dir = self.script_dir.parent.parent / "docs" / "upload"
        
        if not upload_dir.exists():
            raise FileNotFoundError(f"Upload directory not found: {upload_dir}")
        
        pdf_files = list(upload_dir.glob("*.pdf"))
        return sorted(pdf_files)
    
    def print_parse_result(self, parsed_data: Dict[str, Any], show_details: bool = True):
        """
        Print formatted parse result.
        
        Args:
            parsed_data: Result from parse_single_pdf
            show_details: Whether to show detailed course info
        """
        if parsed_data["status"] == "error":
            print(f"❌ Parse FAILED: {parsed_data['file']}")
            print(f"   Error: {parsed_data['error']}")
            return
        
        if not show_details:
            print(f"✅ Parse SUCCESS: {parsed_data['file']}")
            return
        
        data = parsed_data["data"]
        print(f"✅ Parse SUCCESS: {parsed_data['file']}")
        print(f"   Course: {data['course']['code']} - {data['course']['title']}")
        print(f"   Instructor: {data['instructor']['name']}")
        
        offering = data['course_offering']
        print(f"   Term: {offering['quarter']} {offering['year']}")
        if offering.get('section'):
            print(f"   Section: {offering['section']}")
        
        metadata = data.get('metadata', {})
        if metadata:
            print(f"   Comments: {metadata.get('total_comments', 0)}")
            print(f"   Survey Categories: {metadata.get('survey_categories', 0)}")


def test_pdf_processor():
    """Test the PDF processor with a sample file."""
    processor = PDFProcessor()
    
    # Test getting files from upload directory
    try:
        pdf_files = processor.get_upload_directory_files()
        print(f"Found {len(pdf_files)} PDF files in upload directory")
        
        if pdf_files:
            # Test parsing first file
            test_file = pdf_files[0]
            print(f"\nTesting parse of: {test_file.name}")
            result = processor.parse_single_pdf(test_file)
            processor.print_parse_result(result)
            
            if processor.validate_parsed_data(result):
                print("✅ Data is valid for upload")
            else:
                print("❌ Data is NOT valid for upload")
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_pdf_processor()