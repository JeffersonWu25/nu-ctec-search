#!/usr/bin/env python3
"""
Backfill RAG Chunks (Comments) - Populate rag_chunks from comments table.

Creates one rag_chunk per comment with entity_type='course_offering' and
chunk_type='comment'. Builds metadata from canonical tables (comments + joins).

Usage:
    python -m app.jobs.backfill_rag_chunks_comments [--dry-run] [--batch-size N]
"""

import sys
import argparse
import time
from typing import Dict, List, Any

from ..db.unified_rag import (
    fetch_comments_for_rag,
    fetch_existing_rag_chunk_keys,
    insert_rag_chunks
)
from ..utils.logging import get_job_logger


def build_comment_chunk_record(comment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a rag_chunk record from a comment with full context.

    Args:
        comment: Comment dict with nested course_offerings, courses, instructors

    Returns:
        Dict ready for insert into rag_chunks table
    """
    offering = comment['course_offerings']
    course = offering['courses']
    instructor = offering['instructors']

    metadata = {
        'comment_id': comment['id'],
        'course_offering_id': offering['id'],
        'course_id': course['id'],
        'course_code': course['code'],
        'course_title': course['title'],
        'year': offering['year'],
        'quarter': offering['quarter'],
        'section': offering['section'],
        'instructor_id': instructor['id'],
        'instructor_name': instructor['name'],
    }

    return {
        'entity_type': 'course_offering',
        'entity_id': offering['id'],
        'chunk_type': 'comment',
        'content': comment['content'],
        'metadata': metadata
    }


def transform_comments_to_chunks(
    comments: List[Dict[str, Any]],
    existing_comment_ids: set,
    logger
) -> tuple[List[Dict[str, Any]], int]:
    """
    Transform comments into rag_chunk records, skipping existing ones.

    Args:
        comments: List of comment dicts with context
        existing_comment_ids: Set of comment IDs already in rag_chunks
        logger: Logger instance

    Returns:
        Tuple of (chunk_records, skipped_count)
    """
    chunk_records = []
    skipped_existing = 0
    skipped_error = 0

    for comment in comments:
        comment_id = comment.get('id')

        # Skip if already exists
        if comment_id in existing_comment_ids:
            skipped_existing += 1
            continue

        try:
            chunk_record = build_comment_chunk_record(comment)
            chunk_records.append(chunk_record)
        except (KeyError, TypeError) as e:
            logger.warning("Skipping comment %s: %s", comment_id or 'unknown', e)
            skipped_error += 1

    logger.info(
        "Prepared %d chunks, skipped %d existing, %d errors",
        len(chunk_records), skipped_existing, skipped_error
    )

    return chunk_records, skipped_existing


def print_results_summary(
    results: Dict[str, Any],
    total_comments: int,
    skipped_existing: int,
    elapsed_time: float,
    dry_run: bool
):
    """Print job results summary."""
    print("\n" + "=" * 60)
    print("BACKFILL RAG CHUNKS (COMMENTS) RESULTS")
    print("=" * 60)

    print("\nSummary:")
    print(f"  Total comments scanned: {total_comments}")
    print(f"  Skipped (already exists): {skipped_existing}")
    print(f"  Chunks to insert: {results['total']}")
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
    """Main entry point for backfill rag chunks (comments) job."""
    parser = argparse.ArgumentParser(
        description="Backfill rag_chunks table from comments for unified RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.backfill_rag_chunks_comments                  # Run full backfill
  python -m app.jobs.backfill_rag_chunks_comments --dry-run        # Preview without changes
  python -m app.jobs.backfill_rag_chunks_comments --batch-size 50  # Use smaller batches
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

    logger = get_job_logger('backfill_rag_chunks_comments')
    logger.info("Backfill RAG Chunks (Comments) Job Starting")

    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")

    start_time = time.time()

    try:
        # Step 1: Fetch existing comment IDs in rag_chunks for idempotency
        logger.info("Checking existing rag_chunks for comments...")
        existing_comment_ids = fetch_existing_rag_chunk_keys(
            entity_type='course_offering',
            chunk_type='comment',
            key_field='comment_id'
        )
        logger.info("Found %d existing comment chunks", len(existing_comment_ids))

        # Step 2: Fetch all comments with context
        logger.info("Fetching comments with context...")
        comments = fetch_comments_for_rag()
        logger.info("Found %d total comments", len(comments))

        if not comments:
            print("\nNo comments found in database")
            return

        # Step 3: Transform to chunk records (skip existing)
        chunk_records, skipped_existing = transform_comments_to_chunks(
            comments, existing_comment_ids, logger
        )

        if not chunk_records:
            print("\nNo new comments to add to rag_chunks")
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
        print_results_summary(
            results, len(comments), skipped_existing, elapsed_time, args.dry_run
        )

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Backfill job failed: %s", e)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
