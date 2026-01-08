"""
CTEC service - Business logic for CTEC parsing and upload operations.

Orchestrates CTEC processing, validation, and database operations.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..parsing.ctec.ctec_parser import CTECParser, ParserConfig, CTECData
from ..db.courses import get_courses_lookup, get_course_by_code, create_course
from ..db.ctecs import (
    upsert_instructors, 
    upsert_course_offerings,
    upsert_comments,
    upsert_ratings,
    upsert_rating_distributions,
    get_instructors_lookup,
    get_survey_questions_lookup,
    get_ratings_by_offering,
    get_survey_question_options
)
from ..utils.file_helpers import find_pdf_files, confirm_operation
from ..utils.logging import get_job_logger


def parse_and_upload_ctec(pdf_path: Path, dry_run: bool = False, parser_config: Optional[ParserConfig] = None) -> Dict:
    """
    Parse a single CTEC PDF and upload to database.
    
    Args:
        pdf_path: Path to CTEC PDF file
        dry_run: If True, preview changes without applying
        parser_config: Optional parser configuration
        
    Returns:
        Dictionary with parse and upload results
    """
    logger = get_job_logger('upload_ctec')
    
    if not pdf_path.exists():
        return {'error': f'File not found: {pdf_path}'}
    
    if not pdf_path.suffix.lower() == '.pdf':
        return {'error': f'File must be a PDF: {pdf_path}'}
    
    try:
        # Parse CTEC
        logger.info(f"Parsing CTEC: {pdf_path.name}")
        
        if parser_config is None:
            parser_config = ParserConfig(
                debug=False,
                validate_ocr_totals=False,
                continue_on_ocr_errors=True,
                extract_comments=True,
                extract_demographics=True,
                extract_time_survey=True
            )
        
        parser = CTECParser(parser_config)
        ctec_data = parser.parse_ctec(str(pdf_path))
        
        logger.info(f"Successfully parsed CTEC for {ctec_data.course_info.code}")
        
        # Upload to database
        if not dry_run:
            upload_results = upload_ctec_data(ctec_data, pdf_path.name)
        else:
            logger.info("[DRY RUN] Would upload CTEC data")
            upload_results = {
                'uploaded': True,
                'course_offering_id': 'dry-run-id',
                'comments_uploaded': len(ctec_data.comments),
                'ratings_uploaded': len(ctec_data.survey_responses),
                'errors': []
            }
        
        return {
            'status': 'success',
            'file': pdf_path.name,
            'course_info': {
                'code': ctec_data.course_info.code,
                'title': ctec_data.course_info.title,
                'instructor': ctec_data.course_info.instructor,
                'quarter': ctec_data.course_info.quarter,
                'year': ctec_data.course_info.year,
                'section': ctec_data.course_info.section
            },
            'upload_results': upload_results
        }
        
    except Exception as e:
        logger.error(f"Failed to process {pdf_path.name}: {e}")
        return {
            'status': 'error',
            'file': pdf_path.name,
            'error': str(e)
        }


def upload_ctec_data(ctec_data: CTECData, file_identifier: str = "") -> Dict:
    """
    Upload parsed CTEC data to database.
    
    Args:
        ctec_data: Parsed CTEC data
        file_identifier: File name for error reporting
        
    Returns:
        Dictionary with upload results
    """
    logger = get_job_logger('upload_ctec_data')
    
    try:
        # Step 1: Get or create course
        course_lookup = get_courses_lookup()
        course_id = course_lookup.get(ctec_data.course_info.code)
        
        if not course_id:
            # Course doesn't exist - create it from CTEC data
            logger.info(f"Course {ctec_data.course_info.code} not found in database, creating new course record")
            
            created_course = create_course(
                code=ctec_data.course_info.code,
                title=ctec_data.course_info.title,
                department_id=None  # Will be filled in later by department mapping process
            )
            
            if not created_course:
                return {
                    'error': f'Failed to create course record for {ctec_data.course_info.code}'
                }
            
            course_id = created_course['id']
            logger.info(f"Successfully created course record: {ctec_data.course_info.code} (ID: {course_id})")
        
        # Step 2: Upsert instructor
        instructor_data = [{'name': ctec_data.course_info.instructor}]
        instructor_results = upsert_instructors(instructor_data)
        
        if instructor_results['errors']:
            return {'error': f'Failed to upsert instructor: {instructor_results["errors"]}'}
        
        instructor_lookup = get_instructors_lookup()
        instructor_id = instructor_lookup[ctec_data.course_info.instructor]
        
        # Step 3: Upsert course offering
        offering_data = [{
            'course_id': course_id,
            'instructor_id': instructor_id,
            'quarter': ctec_data.course_info.quarter,
            'year': ctec_data.course_info.year,
            'section': ctec_data.course_info.section,
            'audience_size': ctec_data.course_info.audience_size,
            'response_count': ctec_data.course_info.response_count
        }]
        
        offering_results = upsert_course_offerings(offering_data)
        
        if offering_results['errors']:
            return {'error': f'Failed to upsert course offering: {offering_results["errors"]}'}
        
        # Get the course offering ID (we'll need to query for it since upsert may not return it)
        from ..db.ctecs import get_course_offering_by_details
        course_offering = get_course_offering_by_details(
            course_id, instructor_id, 
            ctec_data.course_info.quarter, 
            ctec_data.course_info.year,
            ctec_data.course_info.section
        )
        
        if not course_offering:
            return {'error': 'Failed to retrieve course offering after upload'}
        
        course_offering_id = course_offering['id']
        
        # Step 4: Upload comments
        comments_uploaded = 0
        if ctec_data.comments:
            comment_data = []
            for comment in ctec_data.comments:
                # Create content hash for deduplication
                content_hash = hashlib.sha256(comment.encode('utf-8')).hexdigest()
                comment_data.append({
                    'course_offering_id': course_offering_id,
                    'content': comment,
                    'content_hash': content_hash
                })
            
            comment_results = upsert_comments(comment_data)
            comments_uploaded = comment_results.get('uploaded', 0)
            
            if comment_results['errors']:
                logger.warning(f"Some comments failed to upload: {comment_results['errors']}")
        
        # Step 5: Upload survey responses (questions and ratings)
        ratings_uploaded = 0
        if ctec_data.survey_responses:
            ratings_uploaded = upload_survey_responses(
                course_offering_id, 
                ctec_data.survey_responses
            )
        
        logger.info(f"Successfully uploaded CTEC data: {comments_uploaded} comments, {ratings_uploaded} ratings")
        
        return {
            'uploaded': True,
            'course_offering_id': course_offering_id,
            'comments_uploaded': comments_uploaded,
            'ratings_uploaded': ratings_uploaded,
            'errors': []
        }
        
    except Exception as e:
        logger.error(f"Failed to upload CTEC data for {file_identifier}: {e}")
        return {'error': str(e)}


def upload_survey_responses(course_offering_id: str, survey_responses: Dict[str, Any]) -> int:
    """
    Upload survey questions, ratings, and rating distributions for a course offering.
    
    Args:
        course_offering_id: UUID of the course offering
        survey_responses: Dictionary of survey responses with distributions
        
    Returns:
        Number of ratings uploaded
    """
    logger = get_job_logger('upload_survey')
    
    # Step 1: Get question lookup (questions should already exist from setup)
    questions_lookup = get_survey_questions_lookup()
    
    # Step 2: Create ratings for each question using mapped names
    rating_data = []
    for question_key, response_data in survey_responses.items():
        
        if question_key in questions_lookup:
            question_id = questions_lookup[question_key]
            rating_data.append({
                'course_offering_id': course_offering_id,
                'survey_question_id': question_id
            })
        else:
            logger.warning(f"Question not found after mapping: {question_key}")
    
    # Step 3: Upload ratings (this creates the rating records)
    ratings_uploaded = 0
    if rating_data:
        rating_results = upsert_ratings(rating_data)
        ratings_uploaded = rating_results.get('uploaded', 0)
    
    # Step 4: Upload rating distributions (the actual vote counts)
    if ratings_uploaded > 0:
        upload_rating_distributions(course_offering_id, survey_responses, questions_lookup)
    
    return ratings_uploaded


def upload_rating_distributions(course_offering_id: str, survey_responses: Dict[str, Any], questions_lookup: Dict[str, str]) -> None:
    """
    Upload rating distributions (vote counts) for survey responses.
    
    Args:
        course_offering_id: UUID of the course offering
        survey_responses: Dictionary of survey responses with distributions
        questions_lookup: Dictionary mapping question text to question IDs
    """
    logger = get_job_logger('upload_distributions')
    
    # Get all ratings for this course offering
    ratings = get_ratings_by_offering(course_offering_id)
    rating_lookup = {
        (rating['course_offering_id'], rating['survey_question_id']): rating['id']
        for rating in ratings
    }
    
    distribution_data = []
    
    for question, response_data in survey_responses.items():
        
        if question not in questions_lookup:
            logger.warning(f"Question not found in lookup: {question}")
            continue
            
        question_id = questions_lookup[question]
        rating_key = (course_offering_id, question_id)
        
        if rating_key not in rating_lookup:
            logger.warning(f"No rating found for question: {question}")
            continue
            
        rating_id = rating_lookup[rating_key]
        
        # Get survey question options for this question
        options = get_survey_question_options(question_id)
        if not options:
            logger.warning(f"No options found for question: {question}")
            continue
            
        # Create option lookup: always match by label
        option_lookup = {option['label']: option['id'] for option in options}
        logger.debug(f"Question: {question[:50]}... using label matching with {len(option_lookup)} options")
        
        # Handle distribution data
        if isinstance(response_data, dict):
            # Match each response key to options
            for response_key, count in response_data.items():
                # Convert response key to string to match option labels
                response_key_str = str(response_key)
                if response_key_str in option_lookup:
                    distribution_data.append({
                        'rating_id': rating_id,
                        'option_id': option_lookup[response_key_str],
                        'count': count  # Include zero counts
                    })
                    logger.debug(f"Matched '{response_key}' -> count: {count}")
                else:
                    logger.warning(f"No option found for response key '{response_key}' in question: {question[:30]}...")
                    logger.debug(f"Available options: {list(option_lookup.keys())}")
        else:
            logger.warning(f"Unexpected response format for {question}: {type(response_data)}")
    
    # Upload distribution data
    if distribution_data:
        distribution_results = upsert_rating_distributions(distribution_data)
        logger.info(f"Uploaded {distribution_results.get('uploaded', 0)} rating distributions")
        
        if distribution_results.get('errors'):
            logger.warning(f"Distribution upload errors: {distribution_results['errors']}")
    else:
        logger.warning("No distribution data to upload - check option matching")


def process_ctec_batch(upload_dir: Path, dry_run: bool = False, parser_config: Optional[ParserConfig] = None) -> Dict:
    """
    Process all CTEC PDFs in a directory.
    
    Args:
        upload_dir: Directory containing CTEC PDFs
        dry_run: If True, preview changes without applying
        parser_config: Optional parser configuration
        
    Returns:
        Dictionary with batch processing results
    """
    logger = get_job_logger('batch_ctec')
    logger.info(f"Starting batch CTEC processing from {upload_dir}")
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
    
    # Find PDF files
    pdf_files = find_pdf_files(upload_dir)
    
    if not pdf_files:
        return {'error': f'No PDF files found in {upload_dir}'}
    
    # Confirm processing
    if not dry_run:
        if not confirm_operation(f"Process {len(pdf_files)} CTEC files?"):
            return {'cancelled': True}
    
    # Process files
    results = {
        'total_files': len(pdf_files),
        'successful_uploads': 0,
        'parse_failures': 0,
        'upload_failures': 0,
        'success_rate': 0.0,
        'start_time': datetime.now().isoformat(),
        'files_processed': [],
        'errors': []
    }
    
    for pdf_file in pdf_files:
        result = parse_and_upload_ctec(pdf_file, dry_run=dry_run, parser_config=parser_config)
        
        results['files_processed'].append(result)
        
        if result['status'] == 'success':
            if result['upload_results'].get('uploaded'):
                results['successful_uploads'] += 1
            else:
                results['upload_failures'] += 1
                results['errors'].extend(result['upload_results'].get('errors', []))
        else:
            results['parse_failures'] += 1
            results['errors'].append(f"{result['file']}: {result.get('error', 'Unknown error')}")
        
        logger.info(f"Processed {result['file']}: {result['status']}")
    
    # Calculate final stats
    end_time = datetime.now()
    start_time = datetime.fromisoformat(results['start_time'])
    total_time = str(end_time - start_time)
    
    results['end_time'] = end_time.isoformat()
    results['total_time'] = total_time
    results['success_rate'] = (results['successful_uploads'] / results['total_files']) * 100
    
    logger.info(f"Batch processing complete: {results['successful_uploads']}/{results['total_files']} successful")
    
    return results