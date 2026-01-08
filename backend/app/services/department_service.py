"""
Department service - Business logic for department operations.

Orchestrates department scraping, validation, and database operations.
"""

import re
from typing import Dict, List, Optional
from pathlib import Path

from ..db.departments import (
    get_departments_lookup, 
    upsert_departments,
    get_department_by_code
)
from ..db.courses import (
    get_courses_without_department_id,
    update_courses_department_mapping
)
from ..utils.file_helpers import load_json_file, save_json_file, confirm_operation
from ..utils.logging import get_job_logger
from ..settings import settings


def extract_department_code_from_course(course_code: str) -> Optional[str]:
    """
    Extract department code from course code.
    
    Examples:
        'AFST_101-7' -> 'AFST'
        'AMER_ST_276-0' -> 'AMER_ST'
        'COMP_SCI_150-0' -> 'COMP_SCI'
        'ECON_201' -> 'ECON'
    
    Args:
        course_code: Full course code from database
        
    Returns:
        Department code or None if unable to extract
    """
    if not course_code:
        return None
    
    # Split on underscore
    parts = course_code.split('_')
    
    if len(parts) < 2:
        return None
    
    # Find the first part that contains a number
    dept_parts = []
    for part in parts:
        # If this part starts with a number, we've found the course number
        if re.match(r'^\d', part):
            break
        dept_parts.append(part)
    
    if not dept_parts:
        return None
    
    # Join department parts back with underscore
    return '_'.join(dept_parts)


def scrape_and_upload_departments(dry_run: bool = False) -> Dict:
    """
    Complete workflow: scrape departments from Northwestern catalog and upload to database.
    
    Args:
        dry_run: If True, preview changes without applying
        
    Returns:
        Dictionary with operation results
    """
    logger = get_job_logger('scrape_departments')
    logger.info("Starting department scraping and upload workflow")
    
    try:
        # Import here to avoid circular dependencies
        from ..ingestion.catalog.department_scraper import DepartmentScraper
        
        # Scrape departments
        logger.info("Scraping departments from Northwestern catalog")
        scraper = DepartmentScraper()
        departments_objects = scraper.scrape_departments()
        
        if not departments_objects:
            logger.error("No departments found during scraping")
            return {'error': 'No departments found during scraping'}
        
        logger.info(f"Successfully scraped {len(departments_objects)} departments")
        
        # Convert Department objects to dictionaries for JSON serialization
        departments_data = [
            {'code': dept.code, 'name': dept.name}
            for dept in departments_objects
        ]
        
        # Save backup
        backup_file = settings.SCRAPED_DATA_DIR / "departments_mapping.json"
        save_json_file(departments_data, backup_file, "departments backup")
        
        # Upload to database
        if not dry_run:
            if not confirm_operation(f"Upload {len(departments_data)} departments to database?"):
                return {'cancelled': True, 'backup_file': str(backup_file)}
        
        upload_results = upload_departments_data(departments_data, dry_run=dry_run)
        upload_results['backup_file'] = str(backup_file)
        
        return upload_results
        
    except Exception as e:
        logger.error(f"Department workflow failed: {e}")
        return {'error': str(e)}


def upload_departments_data(departments_data: List[Dict], dry_run: bool = False) -> Dict:
    """
    Upload departments data to database.
    
    Args:
        departments_data: List of department records
        dry_run: If True, preview changes without applying
        
    Returns:
        Dictionary with upload results
    """
    logger = get_job_logger('upload_departments')
    
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    # Validate data structure
    if not departments_data or not isinstance(departments_data, list):
        return {'error': 'Invalid data structure: expected list of departments'}
    
    required_fields = ['code', 'name']
    for i, dept in enumerate(departments_data[:5]):
        for field in required_fields:
            if field not in dept:
                return {'error': f"Missing field '{field}' in department {i+1}"}
    
    logger.info(f"Data validation passed for {len(departments_data)} departments")
    
    # Upload departments
    if not dry_run:
        results = upsert_departments(departments_data)
    else:
        logger.info(f"[DRY RUN] Would upload {len(departments_data)} departments")
        results = {'total': len(departments_data), 'uploaded': len(departments_data), 'errors': []}
    
    return results


def load_departments_from_file(file_path: Path) -> List[Dict]:
    """
    Load departments data from JSON file.
    
    Args:
        file_path: Path to departments JSON file
        
    Returns:
        List of department records
    """
    return load_json_file(file_path, "departments")


def update_course_department_mappings(dry_run: bool = False, sample_size: Optional[int] = None) -> Dict:
    """
    Update department_id column in courses table by extracting department codes.
    
    Args:
        dry_run: If True, preview changes without applying
        sample_size: If provided, only process first N courses
        
    Returns:
        Dictionary with update results
    """
    logger = get_job_logger('update_course_departments')
    
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    # Get courses without department_id
    logger.info("Fetching courses without department_id")
    courses = get_courses_without_department_id()
    
    if not courses:
        logger.info("All courses already have department_id assigned!")
        return {'total_courses': 0, 'matched': 0, 'updated': 0, 'errors': []}
    
    # Apply sample limit if specified
    if sample_size:
        courses = courses[:sample_size]
        logger.info(f"Processing sample of {len(courses)} courses")
    
    # Build department lookup
    logger.info("Building department lookup map")
    dept_lookup = get_departments_lookup()
    
    if not dept_lookup:
        return {'error': 'No departments found in database. Please upload departments first.'}
    
    # Process courses
    results = {
        'total_courses': len(courses),
        'matched': 0,
        'updated': 0,
        'no_match': 0,
        'extraction_failed': 0,
        'errors': []
    }
    
    course_updates = []
    
    for course in courses:
        course_id = course['id']
        course_code = course['code']
        
        # Extract department code
        dept_code = extract_department_code_from_course(course_code)
        
        if not dept_code:
            results['extraction_failed'] += 1
            logger.warning(f"Failed to extract department from: {course_code}")
            continue
        
        # Look up department ID
        if dept_code not in dept_lookup:
            results['no_match'] += 1
            logger.warning(f"No department found for code: {dept_code} (from {course_code})")
            continue
        
        dept_id = dept_lookup[dept_code]
        results['matched'] += 1
        
        course_updates.append({
            'id': course_id,
            'department_id': dept_id
        })
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update {course_code} -> {dept_code} (ID: {dept_id})")
        else:
            logger.info(f"Prepared update: {course_code} -> {dept_code} (ID: {dept_id})")
    
    # Apply updates
    if course_updates and not dry_run:
        update_results = update_courses_department_mapping(course_updates)
        results['updated'] = update_results.get('updated', 0)
        results['errors'].extend(update_results.get('errors', []))
    elif dry_run:
        results['updated'] = len(course_updates)
        logger.info(f"[DRY RUN] Would update {len(course_updates)} courses")
    
    return results