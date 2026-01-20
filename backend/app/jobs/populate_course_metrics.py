#!/usr/bin/env python3
"""
Populate course_metrics table with aggregated ratings across all course offerings.

Computes weighted averages for rating questions and mode for hours per week,
grouped by course.

Usage:
    python -m app.jobs.populate_course_metrics [--dry-run] [--limit N]
"""

import sys
import argparse
import time
from typing import List, Dict

from ..db.course_metrics import (
    get_all_course_ids,
    get_survey_question_id_map,
    compute_metrics_for_course,
    upsert_course_metrics,
    get_course_metrics_stats,
    SURVEY_QUESTION_MAP,
    HOURS_QUESTION_TEXT,
)
from ..utils.logging import get_job_logger


def validate_survey_questions(question_id_map: Dict[str, str]) -> Dict:
    """
    Validate that all required survey questions exist in the database.

    Args:
        question_id_map: Mapping of question text -> question UUID

    Returns:
        Dictionary with validation results
    """
    results = {
        'valid': True,
        'found': [],
        'missing': [],
    }

    # Check rating questions
    for question_text in SURVEY_QUESTION_MAP.keys():
        if question_text in question_id_map:
            results['found'].append(question_text[:50] + "...")
        else:
            results['missing'].append(question_text)
            results['valid'] = False

    # Check hours question
    if HOURS_QUESTION_TEXT in question_id_map:
        results['found'].append(HOURS_QUESTION_TEXT[:50] + "...")
    else:
        results['missing'].append(HOURS_QUESTION_TEXT)
        results['valid'] = False

    return results


def run_populate(args):
    """Run the populate job."""
    logger = get_job_logger('populate_course_metrics')

    print("\n" + "=" * 60)
    print(" POPULATE COURSE METRICS")
    print("=" * 60)

    # Step 1: Load survey question mappings
    print("\n Loading survey question mappings...")
    question_id_map = get_survey_question_id_map()

    if not question_id_map:
        print("\n ERROR: No survey questions found in database.")
        print("        Run setup_survey_questions job first.")
        sys.exit(1)

    print(f"   Found {len(question_id_map)} survey questions in database")

    # Step 2: Validate required questions exist
    print("\n Validating required survey questions...")
    validation = validate_survey_questions(question_id_map)

    if not validation['valid']:
        print("\n ERROR: Missing required survey questions:")
        for missing in validation['missing']:
            print(f"   - \"{missing}\"")
        print("\n        Ensure all CTEC questions are in the survey_questions table.")
        sys.exit(1)

    print(f"   All {len(validation['found'])} required questions found")

    # Step 3: Get all course IDs
    print("\n Fetching courses...")
    course_ids = get_all_course_ids()

    if not course_ids:
        print("\n ERROR: No courses found in database.")
        sys.exit(1)

    if args.limit:
        course_ids = course_ids[:args.limit]
        print(f"   Processing {len(course_ids)} courses (limited)")
    else:
        print(f"   Found {len(course_ids)} courses to process")

    if args.dry_run:
        print(f"\n DRY RUN: Would compute metrics for {len(course_ids)} courses")
        print("          Run without --dry-run to actually populate data")
        return

    # Step 4: Compute metrics for each course
    print(f"\n Computing metrics for {len(course_ids)} courses...")
    print("-" * 60)

    metrics_list: List[Dict] = []
    courses_with_data = 0
    courses_without_data = 0

    for i, course_id in enumerate(course_ids):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"   Processing course {i + 1}/{len(course_ids)}...")

        metrics = compute_metrics_for_course(course_id, question_id_map)

        if metrics:
            metrics_list.append(metrics)
            courses_with_data += 1
        else:
            courses_without_data += 1

    print(f"\n   Courses with rating data: {courses_with_data}")
    print(f"   Courses without rating data: {courses_without_data}")

    if not metrics_list:
        print("\n WARNING: No courses have rating data. Nothing to upsert.")
        return

    # Step 5: Upsert to course_metrics table
    print(f"\n Upserting {len(metrics_list)} course metrics records...")
    print("-" * 60)

    results = upsert_course_metrics(metrics_list)

    # Step 6: Print results
    print("\n" + "=" * 60)
    print(" RESULTS")
    print("=" * 60)
    print(f"   Courses processed: {len(course_ids)}")
    print(f"   Metrics computed: {len(metrics_list)}")
    print(f"   Records upserted: {results['upserted']}")

    if results['errors']:
        print(f"\n   Errors ({len(results['errors'])}):")
        for error in results['errors'][:5]:
            print(f"   - {error}")
        if len(results['errors']) > 5:
            print(f"   ... and {len(results['errors']) - 5} more")


def print_final_stats():
    """Print final course_metrics table statistics."""
    stats = get_course_metrics_stats()
    print(f"\n Course Metrics Table Stats:")
    print(f"   Total records: {stats['total_records']}")
    print(f"   With course rating: {stats.get('with_course_rating', 'N/A')}")
    print(f"   With instruction rating: {stats.get('with_instruction_rating', 'N/A')}")
    print(f"   With hours mode: {stats.get('with_hours_mode', 'N/A')}")


def main():
    """Main entry point for course metrics population job."""
    parser = argparse.ArgumentParser(
        description="Populate course_metrics table with aggregated ratings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.populate_course_metrics                # Process all courses
  python -m app.jobs.populate_course_metrics --dry-run      # Preview without changes
  python -m app.jobs.populate_course_metrics --limit 10     # Process only 10 courses
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without updating database'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of courses to process'
    )

    args = parser.parse_args()

    logger = get_job_logger('populate_course_metrics')
    logger.info("=" * 60)
    logger.info("Course Metrics Population Job Starting")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        run_populate(args)
        print_final_stats()

        elapsed_time = time.time() - start_time
        print(f"\n Time elapsed: {elapsed_time:.1f}s")
        print("\n Job completed!")

    except KeyboardInterrupt:
        print("\n\n Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Job failed: %s", e)
        print(f"\n FATAL ERROR: {e}")
        print("        Check logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
