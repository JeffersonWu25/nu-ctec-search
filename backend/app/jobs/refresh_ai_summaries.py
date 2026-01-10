#!/usr/bin/env python3
"""
AI Summary Refresh Job - Intelligent refresh of AI summaries with staleness detection.

Detects which summaries need updates based on underlying data changes and
regenerates only the necessary summaries in correct dependency order.

Usage:
    python -m app.jobs.refresh_ai_summaries [--dry-run] [--entity-type TYPE] [--force]
"""

import sys
import argparse
import time
from datetime import datetime
from typing import Dict, List

from ..db.ai_summaries import (
    get_stale_course_offerings,
    get_stale_instructors,
    get_stale_courses,
    get_comments_for_offering,
    get_comments_for_instructor,
    get_offering_summaries_for_course,
    upsert_ai_summary
)
from ..utils.ai_helpers import (
    generate_ai_summary,
    prepare_instructor_content,
    validate_summary,
    format_staleness_report
)
from ..utils.logging import get_job_logger




def refresh_course_offering_summaries(stale_offerings: List[Dict], dry_run: bool = False) -> Dict:
    """Refresh AI summaries for stale course offerings."""
    logger = get_job_logger('refresh_ai_summaries')
    logger.info(f"🔄 Refreshing {len(stale_offerings)} course offering summaries")
    
    results = {
        'total': len(stale_offerings),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for offering in stale_offerings:
        offering_id = offering['course_offering_id']
        logger.info(f"Processing offering {offering_id}")
        
        try:
            # Get comments for this offering
            comments = get_comments_for_offering(offering_id)
            
            if not comments:
                logger.warning(f"No comments found for offering {offering_id}")
                results['errors'].append(f"No comments for offering {offering_id}")
                results['failed'] += 1
                continue
            
            if dry_run:
                logger.info(f"DRY RUN: Would generate summary for offering {offering_id} with {len(comments)} comments")
                results['successful'] += 1
                continue
            
            # Generate summary
            summary = generate_ai_summary('course_offering', comments, model="gpt-4o-mini")

            # Validate summary
            validation = validate_summary(summary)
            if not validation['valid']:
                error_msg = f"Invalid summary for offering {offering_id}: {validation['issues']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed'] += 1
                continue
            
            # Save summary
            source_updated_at = datetime.fromisoformat(offering['latest_comment_at'].replace('Z', '+00:00'))
            
            upsert_result = upsert_ai_summary(
                entity_type='course_offering',
                entity_id=offering_id,
                summary=summary,
                model="gpt-4o-mini",
                prompt="course_offering_summary",
                source_updated_at=source_updated_at,
                source_comment_count=len(comments)
            )
            
            if upsert_result['success']:
                logger.info(f"✅ Updated summary for offering {offering_id}")
                results['successful'] += 1
            else:
                logger.error(f"❌ Failed to save summary for offering {offering_id}: {upsert_result['error']}")
                results['errors'].append(f"Save failed for offering {offering_id}")
                results['failed'] += 1
                
        except Exception as e:
            error_msg = f"Exception processing offering {offering_id}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['failed'] += 1
    
    return results


def refresh_instructor_summaries(stale_instructors: List[Dict], dry_run: bool = False) -> Dict:
    """Refresh AI summaries for stale instructors."""
    logger = get_job_logger('refresh_ai_summaries')
    logger.info(f"🔄 Refreshing {len(stale_instructors)} instructor summaries")
    
    results = {
        'total': len(stale_instructors),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for instructor in stale_instructors:
        instructor_id = instructor['instructor_id']
        logger.info(f"Processing instructor {instructor_id}")
        
        try:
            # Get comments across all offerings for this instructor
            comments_data = get_comments_for_instructor(instructor_id)
            
            if not comments_data:
                logger.warning(f"No comments found for instructor {instructor_id}")
                results['errors'].append(f"No comments for instructor {instructor_id}")
                results['failed'] += 1
                continue
            
            if dry_run:
                logger.info(f"DRY RUN: Would generate summary for instructor {instructor_id} with {len(comments_data)} comments")
                results['successful'] += 1
                continue
            
            # Prepare instructor content for summarization
            comment_chunks = prepare_instructor_content(comments_data)

            # Generate summary
            summary = generate_ai_summary('instructor', comment_chunks, model="gpt-4o-mini")
            
            # Validate summary (1500 char max for instructors)
            validation = validate_summary(summary, min_length=200, max_length=1500)
            if not validation['valid']:
                error_msg = f"Invalid summary for instructor {instructor_id}: {validation['issues']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed'] += 1
                continue
            
            # Save summary
            source_updated_at = datetime.fromisoformat(instructor['latest_comment_at'].replace('Z', '+00:00'))
            
            upsert_result = upsert_ai_summary(
                entity_type='instructor',
                entity_id=instructor_id,
                summary=summary,
                model="gpt-4o-mini",
                prompt="instructor_summary",
                source_updated_at=source_updated_at,
                source_comment_count=len(comments_data)
            )
            
            if upsert_result['success']:
                logger.info(f"✅ Updated summary for instructor {instructor_id}")
                results['successful'] += 1
            else:
                logger.error(f"❌ Failed to save summary for instructor {instructor_id}: {upsert_result['error']}")
                results['errors'].append(f"Save failed for instructor {instructor_id}")
                results['failed'] += 1
                
        except Exception as e:
            error_msg = f"Exception processing instructor {instructor_id}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['failed'] += 1
    
    return results


def refresh_course_summaries(stale_courses: List[Dict], dry_run: bool = False) -> Dict:
    """Refresh AI summaries for stale courses."""
    logger = get_job_logger('refresh_ai_summaries')
    logger.info(f"🔄 Refreshing {len(stale_courses)} course summaries")
    
    results = {
        'total': len(stale_courses),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for course in stale_courses:
        course_id = course['course_id']
        logger.info(f"Processing course {course_id}")
        
        try:
            # Get offering summaries for this course
            offering_summaries = get_offering_summaries_for_course(course_id)
            
            if not offering_summaries:
                logger.warning(f"No offering summaries found for course {course_id}")
                results['errors'].append(f"No offering summaries for course {course_id}")
                results['failed'] += 1
                continue
            
            if dry_run:
                logger.info(f"DRY RUN: Would generate summary for course {course_id} using {len(offering_summaries)} offering summaries")
                results['successful'] += 1
                continue
            
            # Generate summary
            summary = generate_ai_summary('course', offering_summaries, model="gpt-4o-mini")
            
            # Validate summary
            validation = validate_summary(summary)
            if not validation['valid']:
                error_msg = f"Invalid summary for course {course_id}: {validation['issues']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed'] += 1
                continue
            
            # Save summary
            source_updated_at = datetime.fromisoformat(course['latest_offering_summary_at'].replace('Z', '+00:00'))
            
            upsert_result = upsert_ai_summary(
                entity_type='course',
                entity_id=course_id,
                summary=summary,
                model="gpt-4o-mini",
                prompt="course_summary",
                source_updated_at=source_updated_at
            )
            
            if upsert_result['success']:
                logger.info(f"✅ Updated summary for course {course_id}")
                results['successful'] += 1
            else:
                logger.error(f"❌ Failed to save summary for course {course_id}: {upsert_result['error']}")
                results['errors'].append(f"Save failed for course {course_id}")
                results['failed'] += 1
                
        except Exception as e:
            error_msg = f"Exception processing course {course_id}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['failed'] += 1
    
    return results


def print_results_summary(results: Dict[str, Dict]):
    """Print comprehensive results summary."""
    print("\n" + "=" * 60)
    print("🎯 AI SUMMARY REFRESH RESULTS")
    print("=" * 60)
    
    total_entities = sum(r['total'] for r in results.values())
    total_successful = sum(r['successful'] for r in results.values())

    success_rate = total_successful / max(total_entities, 1) * 100
    print(f"Overall: {total_successful}/{total_entities} successful ({success_rate:.1f}%)")
    
    for entity_type, result in results.items():
        if result['total'] > 0:
            print(f"\n📊 {entity_type.replace('_', ' ').title()}:")
            print(f"  • Total: {result['total']}")
            print(f"  • Successful: {result['successful']}")
            print(f"  • Failed: {result['failed']}")
            print(f"  • Success rate: {result['successful']/result['total']*100:.1f}%")
            
            if result['errors']:
                print(f"  • First few errors:")
                for error in result['errors'][:3]:
                    print(f"    - {error}")
                if len(result['errors']) > 3:
                    print(f"    - ... and {len(result['errors']) - 3} more")


def main():
    """Main entry point for AI summary refresh job."""
    parser = argparse.ArgumentParser(
        description="AI Summary Refresh System - Intelligently refresh stale AI summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.refresh_ai_summaries                      # Refresh all stale summaries
  python -m app.jobs.refresh_ai_summaries --dry-run           # Preview what would be refreshed
  python -m app.jobs.refresh_ai_summaries --entity-type course_offering  # Only offerings
  python -m app.jobs.refresh_ai_summaries --force             # Force refresh all summaries
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without calling LLM or updating database'
    )
    parser.add_argument(
        '--entity-type',
        choices=['course_offering', 'instructor', 'course'],
        help='Only refresh summaries for specific entity type'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force refresh all summaries regardless of staleness'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('refresh_ai_summaries')
    logger.info("🤖 AI Summary Refresh Job Starting")
    logger.info("=" * 40)
    
    start_time = time.time()
    
    try:
        # 1. Detect stale entities
        print("🔍 Detecting stale summaries...")
        
        stale_data = {}
        
        if not args.entity_type or args.entity_type == 'course_offering':
            stale_data['course_offering'] = get_stale_course_offerings()
        
        if not args.entity_type or args.entity_type == 'instructor':
            # If we're refreshing offerings, also check affected instructors
            affected_instructor_ids = None
            if 'course_offering' in stale_data:
                affected_instructor_ids = [o['instructor_id'] for o in stale_data['course_offering']]
            stale_data['instructor'] = get_stale_instructors(affected_instructor_ids)
        
        if not args.entity_type or args.entity_type == 'course':
            # If we're refreshing offerings, also check affected courses
            affected_course_ids = None
            if 'course_offering' in stale_data:
                affected_course_ids = [o['course_id'] for o in stale_data['course_offering']]
            stale_data['course'] = get_stale_courses(affected_course_ids)
        
        # Print staleness report
        staleness_report = format_staleness_report(stale_data)
        print(staleness_report)
        
        total_stale = sum(len(entities) for entities in stale_data.values())
        if total_stale == 0:
            print("\n✅ No stale summaries found! All AI summaries are up to date.")
            return
        
        if args.dry_run:
            print(f"\n🔍 DRY RUN: Would refresh {total_stale} stale summaries")
            return
        
        print(f"\n🚀 Starting refresh of {total_stale} stale summaries...")
        
        # 2. Refresh summaries in dependency order
        results = {}
        
        # First: Course offerings (no dependencies)
        if 'course_offering' in stale_data and stale_data['course_offering']:
            results['course_offering'] = refresh_course_offering_summaries(
                stale_data['course_offering'], dry_run=False
            )
        
        # Second: Instructors (depend on having comment data)
        if 'instructor' in stale_data and stale_data['instructor']:
            results['instructor'] = refresh_instructor_summaries(
                stale_data['instructor'], dry_run=False
            )
        
        # Third: Courses (depend on having offering summaries)
        if 'course' in stale_data and stale_data['course']:
            results['course'] = refresh_course_summaries(
                stale_data['course'], dry_run=False
            )
        
        # 3. Print results
        print_results_summary(results)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Total time: {elapsed_time:.1f} seconds")
        print("\n🎉 AI summary refresh completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Refresh job failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
