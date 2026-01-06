"""
Upload pipeline orchestrator for parsing and uploading CTEC files.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from pdf_processor import PDFProcessor
from instructor_matcher import InstructorMatcher
from utils import UploadUtils


def validate_extraction_completeness(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate if CTEC extraction was successful based on completeness criteria.
    
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "is_successful": True,
        "issues": [],
        "checks": {
            "course_info": True,
            "instructor_info": True, 
            "term_info": True,
            "survey_categories": True,
            "rating_distributions": True
        }
    }
    
    # Check course information
    course = data.get('course', {})
    if not course.get('code') or not course.get('title'):
        validation_result["checks"]["course_info"] = False
        validation_result["issues"].append("Missing course code or title")
    
    # Check instructor information
    instructor = data.get('instructor', {})
    if not instructor.get('name'):
        validation_result["checks"]["instructor_info"] = False
        validation_result["issues"].append("Missing instructor name")
    
    # Check term information
    offering = data.get('course_offering', {})
    if not offering.get('quarter') or not offering.get('year'):
        validation_result["checks"]["term_info"] = False
        validation_result["issues"].append("Missing quarter or year")
    
    # Check audience size and response count
    if offering.get('audience_size') is None:
        validation_result["checks"]["term_info"] = False
        validation_result["issues"].append("Missing audience size")
    
    if offering.get('response_count') is None:
        validation_result["checks"]["term_info"] = False
        validation_result["issues"].append("Missing response count")
    
    # Check survey categories (should have 10)
    survey_responses = data.get('survey_responses', {})
    if len(survey_responses) < 10:
        validation_result["checks"]["survey_categories"] = False
        validation_result["issues"].append(f"Only {len(survey_responses)}/10 survey categories found")
    
    # Check rating distributions (1-6 scale questions)
    rating_questions = [
        "Provide an overall rating of the instruction",
        "Provide an overall rating of the course", 
        "Estimate how much you learned in the course",
        "Rate the effectiveness of the course in challenging you intellectually",
        "Rate the effectiveness of the instructor in stimulating your interest in the subject"
    ]
    
    rating_issues = []
    for question in rating_questions:
        if question in survey_responses:
            responses = survey_responses[question]
            if isinstance(responses, dict):
                # Check if we have responses for ratings 1-6 (either as strings or integers)
                rating_keys = list(range(1, 7)) + [str(i) for i in range(1, 7)]
                present_ratings = [k for k in rating_keys if k in responses]
                if len(present_ratings) == 0:
                    rating_issues.append(f"{question}: No rating distribution found")
        else:
            rating_issues.append(f"{question}: Missing from survey responses")
    
    if rating_issues:
        validation_result["checks"]["rating_distributions"] = False
        validation_result["issues"].extend(rating_issues)
    
    # Set overall success
    validation_result["is_successful"] = all(validation_result["checks"].values())
    
    return validation_result


class UploadPipeline:
    def __init__(self):
        """Initialize the upload pipeline."""
        self.pdf_processor = PDFProcessor()
        self.instructor_matcher = InstructorMatcher()
        self.upload_utils = UploadUtils()
        
        self.stats = {
            "total_files": 0,
            "successful_uploads": 0,
            "parse_failures": 0,
            "parse_incomplete": 0,
            "upload_failures": 0,
            "start_time": None,
            "end_time": None,
            "failed_files": {
                "parse_failures": [],
                "parse_incomplete": [],
                "upload_failures": []
            }
        }
    
    def process_single_file(self, pdf_path: Path) -> bool:
        """
        Process a single PDF file: parse and upload.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n📄 Processing: {pdf_path.name}")
        print("-" * 50)
        
        # Step 1: Parse the PDF
        print("🔍 Parsing PDF...")
        parsed_data = self.pdf_processor.parse_single_pdf(pdf_path)
        
        if parsed_data["status"] == "error":
            print(f"❌ Parse FAILED: {parsed_data['error']}")
            return False
        
        print("✅ Parse SUCCESS")
        
        # Step 2: Validate parsed data  
        validation_result = validate_extraction_completeness(parsed_data["data"])
        if not validation_result["is_successful"]:
            print(f"❌ Parse INCOMPLETE: {pdf_path.name}")
            for issue in validation_result["issues"]:
                print(f"   - {issue}")
            print("   Skipping upload...")
            return False
        
        print("✅ Validation SUCCESS")
        
        # Step 3: Upload to database
        print("⬆️  Uploading to database...")
        try:
            success = self._upload_ctec_data(parsed_data["data"])
            if success:
                print("✅ Upload SUCCESS")
                return True
            else:
                print("❌ Upload FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Upload ERROR: {e}")
            return False
    
    def process_all_files(self, upload_dir: Path) -> Dict[str, Any]:
        """
        Process all PDF files in the upload directory.
        
        Args:
            upload_dir: Directory containing PDF files
            
        Returns:
            Statistics dictionary
        """
        pdf_files = self.pdf_processor.get_upload_directory_files(upload_dir)
        
        self.stats["total_files"] = len(pdf_files)
        self.stats["start_time"] = datetime.now()
        
        if not pdf_files:
            print("❌ No PDF files found to process")
            return self._finalize_stats()
        
        print(f"Found {len(pdf_files)} PDF files to process\n")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            print("=" * 60)
            
            # Parse the file
            print("🔍 Parsing...")
            parsed_data = self.pdf_processor.parse_single_pdf(pdf_file)
            
            if parsed_data["status"] == "error":
                print(f"❌ Parse FAILED: {parsed_data['error']}")
                self.stats["parse_failures"] += 1
                self.stats["failed_files"]["parse_failures"].append({
                    "file": pdf_file.name,
                    "error": parsed_data['error']
                })
                continue
            
            print("✅ Parse SUCCESS")
            
            # Validate with detailed check
            validation_result = validate_extraction_completeness(parsed_data["data"])
            if not validation_result["is_successful"]:
                print(f"❌ Parse INCOMPLETE: {pdf_file.name}")
                for issue in validation_result["issues"]:
                    print(f"   - {issue}")
                print("   Skipping upload...")
                self.stats["parse_incomplete"] += 1
                self.stats["failed_files"]["parse_incomplete"].append({
                    "file": pdf_file.name,
                    "issues": validation_result["issues"]
                })
                continue
            
            print("✅ Validation SUCCESS")
            
            # Upload
            print("⬆️  Uploading...")
            try:
                success = self._upload_ctec_data(parsed_data["data"])
                if success:
                    print("✅ Upload SUCCESS")
                    self.stats["successful_uploads"] += 1
                else:
                    print("❌ Upload FAILED")
                    self.stats["upload_failures"] += 1
                    self.stats["failed_files"]["upload_failures"].append({
                        "file": pdf_file.name,
                        "error": "Upload failed"
                    })
                    
            except Exception as e:
                print(f"❌ Upload ERROR: {e}")
                self.stats["upload_failures"] += 1
                self.stats["failed_files"]["upload_failures"].append({
                    "file": pdf_file.name,
                    "error": str(e)
                })
        
        return self._finalize_stats()
    
    def _upload_ctec_data(self, ctec_data: Dict[str, Any]) -> bool:
        """
        Upload parsed CTEC data to the database.
        
        Args:
            ctec_data: Parsed CTEC data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Get or create course
            course = self.upload_utils.get_or_create_course(
                ctec_data["course"]["code"],
                ctec_data["course"]["title"]
            )
            print(f"   Course: {course['code']}")
            
            # 2. Get or create instructor
            instructor = self.instructor_matcher.get_or_create_instructor(
                ctec_data["instructor"]["name"]
            )
            print(f"   Instructor: {instructor['name']}")
            
            # 3. Create or update course offering
            offering_data = ctec_data["course_offering"]
            existing_offering = self._check_existing_offering(
                course["id"], instructor["id"], offering_data
            )
            
            if existing_offering:
                print("   Found existing offering, updating...")
                self.upload_utils.clear_existing_offering_data(existing_offering["id"])
                offering = existing_offering
                # Update metadata
                offering = self.upload_utils.create_or_update_course_offering(
                    course["id"], instructor["id"], offering_data
                )
            else:
                print("   Creating new offering...")
                offering = self.upload_utils.create_or_update_course_offering(
                    course["id"], instructor["id"], offering_data
                )
            
            # 4. Insert comments
            comments = ctec_data.get("comments", [])
            if comments:
                comment_ids = self.upload_utils.insert_comments(offering["id"], comments)
                print(f"   Added {len(comment_ids)} comments")
            
            # 5. Insert survey responses
            survey_responses = ctec_data.get("survey_responses", {})
            if survey_responses:
                self.upload_utils.insert_survey_responses(offering["id"], survey_responses)
                print(f"   Added {len(survey_responses)} survey question responses")
            
            return True
            
        except Exception as e:
            print(f"   Database error: {e}")
            return False
    
    def _check_existing_offering(self, course_id: str, instructor_id: str, 
                                offering_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if course offering already exists."""
        sys.path.append(str(Path(__file__).parent.parent))
        from api.supabase_client import supabase
        
        try:
            result = (supabase.table("course_offerings")
                     .select("*")
                     .eq("course_id", course_id)
                     .eq("instructor_id", instructor_id)
                     .eq("quarter", offering_data["quarter"])
                     .eq("year", offering_data["year"])
                     .eq("section", offering_data.get("section"))
                     .execute())
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"   Warning: Error checking existing offering: {e}")
            return None
    
    def _finalize_stats(self) -> Dict[str, Any]:
        """Finalize and return statistics."""
        self.stats["end_time"] = datetime.now()
        
        if self.stats["start_time"]:
            duration = self.stats["end_time"] - self.stats["start_time"]
            self.stats["total_time"] = str(duration).split('.')[0]  # Remove microseconds
        else:
            self.stats["total_time"] = "0:00:00"
        
        total_processed = (self.stats["successful_uploads"] + 
                          self.stats["parse_failures"] + 
                          self.stats["parse_incomplete"] +
                          self.stats["upload_failures"])
        
        if total_processed > 0:
            self.stats["success_rate"] = (self.stats["successful_uploads"] / total_processed) * 100
        else:
            self.stats["success_rate"] = 0.0
        
        return self.stats


def main():
    """Main entry point for direct pipeline usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CTEC Upload Pipeline")
    parser.add_argument("--file", type=str, help="Process single PDF file")
    parser.add_argument("--all", action="store_true", help="Process all files in docs/upload")
    parser.add_argument("--upload-dir", type=str, help="Custom upload directory")
    
    args = parser.parse_args()
    
    pipeline = UploadPipeline()
    
    if args.file:
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            print(f"Error: File not found: {pdf_path}")
            sys.exit(1)
        
        success = pipeline.process_single_file(pdf_path)
        sys.exit(0 if success else 1)
    
    elif args.all:
        upload_dir = Path(args.upload_dir) if args.upload_dir else Path("docs/upload")
        stats = pipeline.process_all_files(upload_dir)
        
        print("\n" + "=" * 60)
        print("📊 BATCH PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total files: {stats['total_files']}")
        print(f"Successfully uploaded: {stats['successful_uploads']}")
        print(f"Parse failures: {stats['parse_failures']}")
        print(f"Parse incomplete: {stats['parse_incomplete']}")
        print(f"Upload failures: {stats['upload_failures']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Total time: {stats['total_time']}")
        
        # Show detailed failure information
        if stats['parse_failures'] > 0:
            print(f"\n❌ Parse Failures ({stats['parse_failures']} files):")
            for failure in stats['failed_files']['parse_failures']:
                print(f"   - {failure['file']}: {failure['error']}")
        
        if stats['parse_incomplete'] > 0:
            print(f"\n⚠️  Parse Incomplete ({stats['parse_incomplete']} files):")
            for incomplete in stats['failed_files']['parse_incomplete']:
                print(f"   - {incomplete['file']}:")
                for issue in incomplete['issues']:
                    print(f"     • {issue}")
        
        if stats['upload_failures'] > 0:
            print(f"\n💾 Upload Failures ({stats['upload_failures']} files):")
            for failure in stats['failed_files']['upload_failures']:
                print(f"   - {failure['file']}: {failure['error']}")
        
        # Determine exit code
        has_failures = (stats['parse_failures'] > 0 or 
                       stats['parse_incomplete'] > 0 or 
                       stats['upload_failures'] > 0)
        sys.exit(1 if has_failures else 0)
    
    else:
        print("Error: Must specify --file or --all")
        sys.exit(1)


if __name__ == "__main__":
    main()