#!/usr/bin/env python3
"""
Batch CTEC Parser Script

Processes all CTEC PDF files in docs/samples and outputs structured JSON
ready for database upload. Handles errors gracefully and continues processing.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from ctec_parser import CTECParser, ParserConfig


def validate_extraction_success(data: Dict[str, Any]) -> Dict[str, Any]:
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


def create_course_record(course_info) -> Dict[str, Any]:
    """Create course record for courses table."""
    return {
        "code": course_info.code,
        "title": course_info.title
    }


def create_instructor_record(course_info) -> Dict[str, Any]:
    """Create instructor record for instructors table."""
    return {
        "name": course_info.instructor
    }


def create_course_offering_record(course_info) -> Dict[str, Any]:
    """Create course offering record for course_offerings table."""
    section = None
    if course_info.section and course_info.section.isdigit():
        section = int(course_info.section)

    return {
        "quarter": course_info.quarter,
        "year": course_info.year,
        "audience_size": None,
        "response_count": None,
        "section": section
    }


def create_comment_records(comments: List[str]) -> List[Dict[str, Any]]:
    """Create comment records for comments table."""
    comment_records = []
    for comment in comments:
        comment_records.append({
            "content": comment
        })
    return comment_records


def create_survey_responses_records(survey_responses: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """Create survey responses in human-readable format."""
    # Map the actual question names from OCR to display names
    question_mapping = {
        "Provide an overall rating of the instruction": "Provide an overall rating of the instruction",
        "Provide an overall rating of the course": "Provide an overall rating of the course", 
        "Estimate how much you learned in the course": "Estimate how much you learned in the course",
        "Rate the effectiveness of the course in challenging you intellectually": "Rate the effectiveness of the course in challenging you intellectually",
        "Rate the effectiveness of the instructor in stimulating your interest in the subject": "Rate the effectiveness of the instructor in stimulating your interest in the subject",
        "school_name": "School/Department",
        "class_year": "Class Year",
        "reason_for_taking_course": "Reason for taking course",
        "prior_interest": "Prior interest level",
        "Estimate the average number of hours per week you spent on this course outside of class and lab time": "Hours per week spent on coursework"
    }
    
    structured_responses = {}
    
    for question_name, data in survey_responses.items():
        if question_name in question_mapping and data:
            display_name = question_mapping[question_name]
            structured_responses[display_name] = data
        elif data:  # Pass through unmapped questions as-is
            structured_responses[question_name] = data
            
    return structured_responses


def process_single_ctec(parser: CTECParser, pdf_path: Path) -> Dict[str, Any]:
    """
    Process a single CTEC file and return structured data.
    
    Returns:
        Dictionary with parsed data or error information
    """
    print(f"Processing: {pdf_path.name}")
    
    try:
        # Parse the CTEC
        ctec_data = parser.parse_ctec(str(pdf_path))

        # Create structured records
        course_record = create_course_record(ctec_data.course_info)
        instructor_record = create_instructor_record(ctec_data.course_info)
        course_offering_record = create_course_offering_record(ctec_data.course_info)
        comment_records = create_comment_records(ctec_data.comments)
        survey_responses = create_survey_responses_records(ctec_data.survey_responses)
        
        return {
            "status": "success",
            "file": pdf_path.name,
            "data": {
                "course": course_record,
                "instructor": instructor_record,
                "course_offering": course_offering_record,
                "comments": comment_records,
                "survey_responses": survey_responses,
                "metadata": {
                    "total_comments": len(ctec_data.comments),
                    "survey_categories": len(survey_responses),
                    "parsed_at": datetime.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        error_msg = f"Failed to parse {pdf_path.name}: {str(e)}"
        print(f"  ✗ {error_msg}")
        
        return {
            "status": "error",
            "file": pdf_path.name,
            "error": str(e),
            "error_type": type(e).__name__
        }


def main():
    """Main batch processing function."""
    # Setup paths
    script_dir = Path(__file__).parent
    samples_dir = script_dir.parent.parent / "docs" / "samples"
    output_file = script_dir / "parsed_ctecs.json"
    
    print(f"CTEC Batch Parser")
    print(f"================")
    print(f"Samples directory: {samples_dir}")
    print(f"Output file: {output_file}")
    print()
    
    # Check if samples directory exists
    if not samples_dir.exists():
        print(f"Error: Samples directory not found: {samples_dir}")
        sys.exit(1)
    
    # Find all PDF files
    pdf_files = list(samples_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"Error: No PDF files found in {samples_dir}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files to process")
    print()
    
    # Initialize parser
    config = ParserConfig(
        debug=False,  # Set to True for verbose output
        validate_ocr_totals=False,  # Disable strict OCR validation to allow extraction even with minor total mismatches
        continue_on_ocr_errors=True,
        extract_comments=True,
        extract_demographics=True,
        extract_time_survey=True
    )
    parser = CTECParser(config)
    
    # Process all files
    results = []
    successful = 0
    failed = 0
    
    for pdf_file in sorted(pdf_files):
        result = process_single_ctec(parser, pdf_file)
        results.append(result)
        
        if result["status"] == "success":
            data = result['data']
            metadata = data['metadata']
            
            # Validate extraction completeness
            validation = validate_extraction_success(data)
            
            if validation["is_successful"]:
                successful += 1
                status_symbol = "✓ COMPLETE"
            else:
                failed += 1
                status_symbol = "⚠ INCOMPLETE"
            
            # Print all parsed CTEC details except comments
            print(f"  {status_symbol}: {data['course']['code']} - {data['course']['title']}")
            print(f"    Instructor: {data['instructor']['name']}")
            print(f"    Term: {data['course_offering']['quarter']} {data['course_offering']['year']}")
            print(f"    Section: {data['course_offering']['section'] or 'N/A'}")
            print(f"    Audience Size: {data['course_offering']['audience_size'] or 'N/A'}")
            print(f"    Response Count: {data['course_offering']['response_count'] or 'N/A'}")
            print(f"    Comments: {metadata['total_comments']} found")
            print(f"    Survey Categories: {metadata['survey_categories']}")
            
            # Show validation issues if any
            if not validation["is_successful"]:
                print(f"    Issues: {'; '.join(validation['issues'])}")
            
            # Print survey responses
            if data['survey_responses']:
                print(f"    Survey Responses:")
                for question, responses in data['survey_responses'].items():
                    if isinstance(responses, dict) and responses:
                        total_responses = sum(responses.values())
                        print(f"      {question}: {total_responses} responses")
                        # Print distribution
                        response_details = []
                        for rating, count in sorted(responses.items()):
                            if isinstance(rating, (int, str)) and str(rating).isdigit():
                                response_details.append(f"{rating}({count})")
                            else:
                                response_details.append(f"{rating}({count})")
                        print(f"        Distribution: {', '.join(response_details)}")
            
            print(f"    Parsed at: {metadata['parsed_at']}")
            print()
        else:
            failed += 1
            print(f"  ✗ FAILED: {result['file']}: {result['error']}")
            print()
    
    # Create final output structure
    output_data = {
        "batch_info": {
            "processed_at": datetime.now().isoformat(),
            "total_files": len(pdf_files),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(pdf_files)*100):.1f}%"
        },
        "ctec_records": results
    }
    
    # Write to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print()
        print("Results Summary:")
        print("================")
        print(f"📊 Total Files: {len(pdf_files)}")
        print(f"✓ Complete Extractions: {successful}")
        print(f"⚠ Incomplete Extractions: {failed - len([r for r in results if r['status'] == 'error'])}")
        print(f"✗ Parse Failures: {len([r for r in results if r['status'] == 'error'])}")
        print(f"📈 Success Rate: {(successful/len(pdf_files)*100):.1f}%")
        print(f"📁 Output saved to: {output_file}")
        
        # Show incomplete extractions
        incomplete_files = []
        parse_failed_files = []
        
        for result in results:
            if result["status"] == "error":
                parse_failed_files.append((result['file'], result['error']))
            elif result["status"] == "success":
                validation = validate_extraction_success(result['data'])
                if not validation["is_successful"]:
                    incomplete_files.append((result['file'], validation['issues']))
        
        if incomplete_files:
            print(f"\n⚠ Incomplete Extractions ({len(incomplete_files)} files):")
            for file_name, issues in incomplete_files:
                print(f"  - {file_name}: {'; '.join(issues)}")
        
        if parse_failed_files:
            print(f"\n✗ Parse Failures ({len(parse_failed_files)} files):")
            for file_name, error in parse_failed_files:
                print(f"  - {file_name}: {error}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()