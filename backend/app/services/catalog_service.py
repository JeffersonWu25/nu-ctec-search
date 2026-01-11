"""
Catalog service - Business logic for course catalog operations.

Orchestrates catalog scraping, validation, and database operations.
"""

from typing import Dict, List, Set, Any
from pathlib import Path

from ..db.courses import get_courses_lookup, update_course_descriptions, get_courses_with_empty_catalog_data
from ..db.requirements import (
    get_requirements_lookup, 
    upsert_requirements_from_names,
    update_course_requirements
)
from ..utils.file_helpers import load_json_file, save_json_file, confirm_operation
from ..utils.logging import get_job_logger
from ..settings import settings
from ..supabase_client import supabase


def scrape_and_upload_catalog(dry_run: bool = False, department_filter: List[str] = None, limit_departments: int = None, empty_courses_only: bool = False) -> Dict:
    """
    Complete workflow: scrape course catalog and upload to database.
    
    Args:
        dry_run: If True, preview changes without applying
        department_filter: Optional list of department codes to scrape
        limit_departments: Optional limit on number of departments
        empty_courses_only: If True, only update courses with completely empty catalog data
        
    Returns:
        Dictionary with operation results
    """
    logger = get_job_logger('scrape_catalog')
    logger.info("Starting catalog scraping and upload workflow")
    
    try:
        # Import here to avoid circular dependencies
        from ..ingestion.catalog.scraper import CatalogScraper
        
        # Scrape catalog
        logger.info("Scraping course catalog from Northwestern")
        scraper = CatalogScraper(output_dir=str(settings.SCRAPED_DATA_DIR))
        scraped_data = scraper.scrape_all(
            limit_departments=limit_departments,
            department_filter=department_filter
        )
        
        if not scraped_data.courses:
            logger.error("No courses found during scraping")
            return {'error': 'No courses found during scraping'}
        
        logger.info(f"Successfully scraped {len(scraped_data.courses)} courses")
        
        # Get department scraping results for validation
        department_results = scraper.get_department_results()
        
        # Convert to upload format
        catalog_data = [
            {
                'course_code': course.course_code,
                'description': course.description or '',
                'prerequisites_text': course.prerequisites_text or '',
                'requirements': course.requirements or []
            }
            for course in scraped_data.courses
        ]
        
        # Save backup
        backup_file = settings.SCRAPED_DATA_DIR / "catalog_data.json"
        save_json_file(catalog_data, backup_file, "catalog backup")
        
        # Upload to database
        if not dry_run:
            if not confirm_operation(f"Upload {len(catalog_data)} course updates to database?"):
                return {'cancelled': True, 'backup_file': str(backup_file)}
        
        upload_results = update_course_catalog_data(catalog_data, dry_run=dry_run, empty_courses_only=empty_courses_only)
        upload_results['backup_file'] = str(backup_file)
        upload_results['department_results'] = department_results
        
        return upload_results
        
    except Exception as e:
        logger.error(f"Catalog workflow failed: {e}")
        return {'error': str(e)}


def load_catalog_from_file(file_path: Path) -> List[Dict]:
    """
    Load catalog data from JSON file.
    
    Args:
        file_path: Path to catalog JSON file
        
    Returns:
        List of course records
    """
    return load_json_file(file_path, "catalog data")


def validate_catalog_data(catalog_data: List[Dict]) -> bool:
    """
    Validate catalog data structure.
    
    Args:
        catalog_data: List of course records
        
    Returns:
        True if validation passes, False otherwise
    """
    if not catalog_data or not isinstance(catalog_data, list):
        print("❌ Invalid data: expected list of courses")
        return False
    
    required_fields = ['course_code', 'description', 'prerequisites_text', 'requirements']
    
    for i, course in enumerate(catalog_data[:5]):  # Check first 5 courses
        for field in required_fields:
            if field not in course:
                print(f"❌ Missing field '{field}' in course {i+1}")
                return False
    
    print("✅ Data validation passed")
    return True


def extract_unique_requirements(catalog_data: List[Dict]) -> Set[str]:
    """
    Extract all unique requirement names from catalog data.
    
    Args:
        catalog_data: List of course records
        
    Returns:
        Set of unique requirement names
    """
    all_requirements = set()
    for course in catalog_data:
        all_requirements.update(course.get('requirements', []))
    
    # Remove empty strings
    all_requirements.discard('')
    return all_requirements


def filter_to_existing_courses(catalog_data: List[Dict], courses_map: Dict[str, str]) -> Dict:
    """
    Filter catalog data to only courses that exist in database.
    
    Args:
        catalog_data: List of course records from catalog
        courses_map: Dictionary mapping course code to course id
        
    Returns:
        Dictionary with matched and missing course data
    """
    logger = get_job_logger('catalog_filter')
    logger.info("Filtering catalog data to existing courses only")
    
    matched_courses = []
    missing_courses = []
    
    for course_data in catalog_data:
        course_code = course_data['course_code']
        
        if course_code in courses_map:
            matched_courses.append(course_data)
        else:
            missing_courses.append(course_code)
    
    logger.info(f"✅ {len(matched_courses)} courses found in database")
    logger.info(f"❌ {len(missing_courses)} courses NOT found (will be skipped)")
    
    if missing_courses:
        logger.info("📝 Sample missing courses:")
        for course_code in missing_courses[:10]:
            logger.info(f"   • {course_code}")
        if len(missing_courses) > 10:
            logger.info(f"   ... and {len(missing_courses) - 10} more")
    
    return {
        'matched_data': matched_courses,
        'missing_courses': missing_courses
    }


def prepare_course_updates(matched_data: List[Dict], courses_map: Dict[str, str]) -> List[Dict]:
    """
    Prepare course update records for batch update.
    
    Args:
        matched_data: List of course data that matched existing courses
        courses_map: Dictionary mapping course code to course id
        
    Returns:
        List of update records with id and fields to update
    """
    logger = get_job_logger('catalog_prepare')
    logger.info("Preparing course updates")
    
    course_updates = []
    
    for course_data in matched_data:
        course_code = course_data['course_code']
        course_id = courses_map[course_code]
        
        # Prepare update record (ID + fields to update)
        update_record = {
            'id': course_id,
            'description': course_data['description'],
            'prerequisites_text': course_data['prerequisites_text']
        }
        
        course_updates.append(update_record)
    
    logger.info(f"✅ Prepared {len(course_updates)} course updates")
    return course_updates


def prepare_course_requirements(matched_data: List[Dict], courses_map: Dict[str, str], requirements_map: Dict[str, str]) -> Dict:
    """
    Prepare course-requirements link data for matched courses only.
    
    Args:
        matched_data: List of course data that matched existing courses
        courses_map: Dictionary mapping course code to course id
        requirements_map: Dictionary mapping requirement name to requirement id
        
    Returns:
        Dictionary with course-requirement pairs and course IDs
    """
    logger = get_job_logger('catalog_requirements')
    logger.info("Preparing course-requirements links")
    
    course_requirement_pairs = []
    matched_course_ids = set()
    
    for course_data in matched_data:
        course_code = course_data['course_code']
        course_id = courses_map[course_code]  # Safe since data is already filtered
        matched_course_ids.add(course_id)
        
        requirements = course_data.get('requirements', [])
        
        # Create pairs for each requirement
        for req_name in requirements:
            if req_name and req_name in requirements_map:
                course_requirement_pairs.append({
                    'course_id': course_id,
                    'requirement_id': requirements_map[req_name]
                })
    
    logger.info(f"✅ Created {len(course_requirement_pairs)} course-requirement links")
    logger.info(f"📚 Links for {len(matched_course_ids)} matched courses")
    
    return {
        'pairs': course_requirement_pairs,
        'course_ids': list(matched_course_ids)
    }


def update_course_catalog_data(catalog_data: List[Dict], dry_run: bool = False, empty_courses_only: bool = False) -> Dict[str, Any]:
    """
    Update course catalog data in database (UPDATE ONLY - no inserts).
    
    Args:
        catalog_data: List of course dictionaries from JSON
        dry_run: If True, preview changes without applying
        empty_courses_only: If True, only update courses with completely empty catalog data
        
    Returns:
        Dictionary with upload results and statistics
    """
    logger = get_job_logger('update_catalog')
    logger.info("Starting catalog data update (UPDATE ONLY MODE)")
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
    
    # Step 1: Validate data
    if not validate_catalog_data(catalog_data):
        return {'error': 'Data validation failed'}
    
    # Step 2: Build lookup maps
    logger.info("Building lookup maps")
    if empty_courses_only:
        logger.info("🔍 EMPTY COURSES ONLY mode - filtering to courses with no catalog data")
        # Get only courses that have empty catalog data
        empty_courses = get_courses_with_empty_catalog_data()
        courses_map = {course['code']: course['id'] for course in empty_courses}
        logger.info(f"Found {len(courses_map)} courses with empty catalog data")
    else:
        courses_map = get_courses_lookup()
    
    requirements_map = get_requirements_lookup()
    
    # Step 3: Filter to existing courses only
    filter_results = filter_to_existing_courses(catalog_data, courses_map)
    matched_data = filter_results['matched_data']
    missing_courses = filter_results['missing_courses']
    
    if not matched_data:
        logger.error("No courses matched existing database records. Nothing to update.")
        return {
            'total_courses': len(catalog_data),
            'courses_matched': 0,
            'courses_updated': 0,
            'courses_missing': missing_courses,
            'requirements_found': 0,
            'requirements_linked': 0,
            'errors': [],
            'dry_run': dry_run
        }
    
    # Step 4: Upsert requirements for matched courses
    unique_requirements = extract_unique_requirements(matched_data)
    logger.info(f"📋 Found {len(unique_requirements)} unique requirements in matched courses")
    
    if not dry_run and unique_requirements:
        req_results = upsert_requirements_from_names(unique_requirements)
        # Update lookup map with new requirements
        requirements_map.update(req_results.get('lookup_map', {}))
    else:
        logger.info("   [DRY RUN] Would upsert requirements")
    
    # Step 5: Prepare and update courses (EXISTING ONLY)
    course_updates = prepare_course_updates(matched_data, courses_map)
    
    # Validate that all course IDs in updates actually exist in database
    if course_updates:
        update_ids = [update['id'] for update in course_updates]
        response = supabase.table('courses').select('id').in_('id', update_ids).execute()
        existing_ids = {record['id'] for record in response.data}
        
        valid_updates = [u for u in course_updates if u['id'] in existing_ids]
        skipped_count = len(course_updates) - len(valid_updates)
        
        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} course updates with invalid IDs")
        
        course_updates = valid_updates
    
    if not dry_run and course_updates:
        course_results = update_course_descriptions(course_updates)
    else:
        if dry_run:
            logger.info(f"   [DRY RUN] Would update {len(course_updates)} existing courses")
        course_results = {'total': len(course_updates), 'updated': len(course_updates), 'errors': []}
    
    # Step 6: Prepare and update course-requirements (MATCHED COURSES ONLY)
    req_prep = prepare_course_requirements(matched_data, courses_map, requirements_map)
    
    if not dry_run:
        requirements_results = update_course_requirements(
            req_prep['course_ids'], 
            req_prep['pairs']
        )
    else:
        logger.info(f"   [DRY RUN] Would link {len(req_prep['pairs'])} course-requirement pairs")
        requirements_results = {'cleared': 0, 'linked': len(req_prep['pairs']), 'errors': []}
    
    # Compile results
    results = {
        'total_courses': len(catalog_data),
        'courses_matched': len(matched_data),
        'courses_updated': course_results.get('updated', 0),
        'courses_missing': missing_courses,
        'requirements_found': len(unique_requirements),
        'requirements_linked': requirements_results.get('linked', 0),
        'errors': course_results.get('errors', []) + requirements_results.get('errors', []),
        'dry_run': dry_run
    }
    
    return results