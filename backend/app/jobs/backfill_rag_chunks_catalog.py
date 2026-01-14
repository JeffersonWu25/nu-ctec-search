#!/usr/bin/env python3
"""
Backfill RAG Chunks (Catalog) - Populate rag_chunks from courses table.

Creates separate chunks for:
- catalog_description: course.description
- catalog_prereqs: course.prerequisites_text

Each chunk has entity_type='course' and appropriate metadata.

Usage:
    python -m app.jobs.backfill_rag_chunks_catalog [--dry-run] [--batch-size N]
"""

import sys
import argparse
import time
from typing import Dict, List, Any, Optional

from ..db.unified_rag import (
    fetch_courses_for_rag,
    fetch_existing_catalog_chunks,
    insert_rag_chunks
)
from ..utils.logging import get_job_logger


def build_catalog_chunk_record(
    course: Dict[str, Any],
    chunk_type: str,
    content: str
) -> Dict[str, Any]:
    """
    Build a rag_chunk record for a catalog chunk.

    Args:
        course: Course dict with department data
        chunk_type: 'catalog_description' or 'catalog_prereqs'
        content: The text content (description or prereqs)

    Returns:
        Dict ready for insert into rag_chunks table
    """
    department = course.get('departments') or {}

    metadata = {
        'course_id': course['id'],
        'course_code': course['code'],
        'course_title': course['title'],
        'department_id': department.get('id'),
        'department_code': department.get('code'),
        'department_name': department.get('name'),
    }

    return {
        'entity_type': 'course',
        'entity_id': course['id'],
        'chunk_type': chunk_type,
        'content': content,
        'metadata': metadata
    }


def transform_courses_to_chunks(
    courses: List[Dict[str, Any]],
    existing_chunks: Dict[str, set],
    logger
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Transform courses into rag_chunk records for description and prereqs.

    Args:
        courses: List of course dicts with department data
        existing_chunks: Dict mapping course_id -> set of existing chunk_types
        logger: Logger instance

    Returns:
        Tuple of (chunk_records, stats_dict)
    """
    chunk_records = []
    stats = {
        'skipped_no_description': 0,
        'skipped_no_prereqs': 0,
        'skipped_existing_description': 0,
        'skipped_existing_prereqs': 0,
        'added_description': 0,
        'added_prereqs': 0,
        'errors': 0
    }

    for course in courses:
        course_id = course.get('id')
        existing_types = existing_chunks.get(course_id, set())

        try:
            # Handle description chunk
            description = (course.get('description') or '').strip()
            if not description:
                stats['skipped_no_description'] += 1
            elif 'catalog_description' in existing_types:
                stats['skipped_existing_description'] += 1
            else:
                chunk = build_catalog_chunk_record(
                    course, 'catalog_description', description
                )
                chunk_records.append(chunk)
                stats['added_description'] += 1

            # Handle prerequisites chunk
            prereqs = (course.get('prerequisites_text') or '').strip()
            if not prereqs:
                stats['skipped_no_prereqs'] += 1
            elif 'catalog_prereqs' in existing_types:
                stats['skipped_existing_prereqs'] += 1
            else:
                chunk = build_catalog_chunk_record(
                    course, 'catalog_prereqs', prereqs
                )
                chunk_records.append(chunk)
                stats['added_prereqs'] += 1

        except (KeyError, TypeError) as e:
            logger.warning("Skipping course %s: %s", course_id or 'unknown', e)
            stats['errors'] += 1

    logger.info(
        "Prepared %d chunks: %d descriptions, %d prereqs",
        len(chunk_records), stats['added_description'], stats['added_prereqs']
    )

    return chunk_records, stats


def print_results_summary(
    results: Dict[str, Any],
    total_courses: int,
    stats: Dict[str, int],
    elapsed_time: float,
    dry_run: bool
):
    """Print job results summary."""
    print("\n" + "=" * 60)
    print("BACKFILL RAG CHUNKS (CATALOG) RESULTS")
    print("=" * 60)

    print("\nCourses Scanned:")
    print(f"  Total courses: {total_courses}")

    print("\nDescription Chunks:")
    print(f"  Added: {stats['added_description']}")
    print(f"  Skipped (no content): {stats['skipped_no_description']}")
    print(f"  Skipped (already exists): {stats['skipped_existing_description']}")

    print("\nPrerequisites Chunks:")
    print(f"  Added: {stats['added_prereqs']}")
    print(f"  Skipped (no content): {stats['skipped_no_prereqs']}")
    print(f"  Skipped (already exists): {stats['skipped_existing_prereqs']}")

    print("\nInsert Results:")
    print(f"  Total chunks to insert: {results['total']}")
    print(f"  Inserted: {results['inserted']}")

    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        print("\nErrors:")
        for error in results['errors'][:5]:
            print(f"    - {error}")
        if len(results['errors']) > 5:
            print(f"    - ... and {len(results['errors']) - 5} more")
    else:
        print("  Errors: 0")

    if results['total'] > 0:
        success_rate = results['inserted'] / results['total'] * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")

    print(f"Time: {elapsed_time:.1f} seconds")

    if dry_run:
        print("\nDRY RUN completed - no changes were made")


def main():
    """Main entry point for backfill rag chunks (catalog) job."""
    parser = argparse.ArgumentParser(
        description="Backfill rag_chunks table from courses (catalog) for unified RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.backfill_rag_chunks_catalog                  # Run full backfill
  python -m app.jobs.backfill_rag_chunks_catalog --dry-run        # Preview without changes
  python -m app.jobs.backfill_rag_chunks_catalog --batch-size 50  # Use smaller batches
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of records per batch (default: 100)'
    )

    args = parser.parse_args()

    logger = get_job_logger('backfill_rag_chunks_catalog')
    logger.info("Backfill RAG Chunks (Catalog) Job Starting")

    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")

    start_time = time.time()

    try:
        # Step 1: Fetch existing catalog chunks for idempotency
        logger.info("Checking existing catalog chunks...")
        existing_chunks = fetch_existing_catalog_chunks()
        logger.info(
            "Found existing chunks for %d courses",
            len(existing_chunks)
        )

        # Step 2: Fetch all courses with department info
        logger.info("Fetching courses...")
        courses = fetch_courses_for_rag()
        logger.info("Found %d courses", len(courses))

        if not courses:
            print("\nNo courses found in database")
            return

        # Step 3: Transform to chunk records (skip existing/empty)
        chunk_records, stats = transform_courses_to_chunks(
            courses, existing_chunks, logger
        )

        if not chunk_records:
            print("\nNo new catalog chunks to add")
            elapsed_time = time.time() - start_time
            print(f"Time: {elapsed_time:.1f} seconds")
            return

        # Step 4: Insert chunks
        if args.dry_run:
            results = {
                'total': len(chunk_records),
                'inserted': len(chunk_records),
                'errors': []
            }
            logger.info("DRY RUN: Would insert %d chunks", len(chunk_records))
        else:
            logger.info("Inserting %d chunks...", len(chunk_records))
            results = insert_rag_chunks(chunk_records, batch_size=args.batch_size)

        # Print summary
        elapsed_time = time.time() - start_time
        print_results_summary(results, len(courses), stats, elapsed_time, args.dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Backfill job failed: %s", e)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
