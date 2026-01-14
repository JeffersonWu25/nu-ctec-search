#!/usr/bin/env python3
"""
# DEPRECATED: comment_chunks + embeddings
# Superseded by rag_chunks + rag_embeddings.
# Use backfill_rag_chunks_comments.py instead.

Backfill Comment Chunks Job - Populate comment_chunks table from comments.

Creates 1:1 mapping from comments to comment_chunks with metadata for RAG.
This is the first step in enabling entity-specific RAG for course offerings.

Usage:
    python -m app.jobs.backfill_comment_chunks [--dry-run] [--batch-size N]
"""

import sys
import argparse
import time
from typing import Dict, List, Any

from ..db.rag import fetch_comments_with_context, upsert_comment_chunks
from ..utils.logging import get_job_logger
from ..rag.chunking import build_chunk_metadata, build_chunk_record, ChunkContext


def transform_to_chunk_records(
    comments: List[Dict[str, Any]],
    logger
) -> List[Dict[str, Any]]:
    """Transform fetched comments into chunk records ready for upsert."""
    chunk_records = []
    skipped = 0

    for comment in comments:
        try:
            offering = comment['course_offerings']
            course = offering['courses']
            instructor = offering['instructors']

            context: ChunkContext = {
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

            metadata = build_chunk_metadata(context)
            chunk_record = build_chunk_record(
                comment_id=comment['id'],
                course_offering_id=comment['course_offering_id'],
                content=comment['content'],
                metadata=metadata,
            )

            chunk_records.append(chunk_record)

        except (KeyError, TypeError) as e:
            logger.warning("Skipping comment %s: %s", comment.get('id', 'unknown'), e)
            skipped += 1

    logger.info("Transformed %d comments, skipped %d", len(chunk_records), skipped)
    return chunk_records


def print_results_summary(results: Dict[str, Any], elapsed_time: float, dry_run: bool):
    """Print job results summary."""
    print("\n" + "=" * 60)
    print("BACKFILL COMMENT CHUNKS RESULTS")
    print("=" * 60)

    print("\nSummary:")
    print(f"  Total comments: {results['total']}")
    print(f"  Upserted chunks: {results['upserted']}")

    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        print("\nErrors:")
        for error in results['errors'][:5]:
            print(f"    - {error}")
        if len(results['errors']) > 5:
            print(f"    - ... and {len(results['errors']) - 5} more")
    else:
        print("  Errors: 0")

    success_rate = results['upserted'] / max(results['total'], 1) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    print(f"Time: {elapsed_time:.1f} seconds")

    if dry_run:
        print("\nDRY RUN completed - no changes were made")


def main():
    """Main entry point for backfill comment chunks job."""
    parser = argparse.ArgumentParser(
        description="Backfill comment_chunks table from comments for RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.backfill_comment_chunks                  # Run full backfill
  python -m app.jobs.backfill_comment_chunks --dry-run        # Preview without changes
  python -m app.jobs.backfill_comment_chunks --batch-size 50  # Use smaller batches
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

    logger = get_job_logger('backfill_comment_chunks')
    logger.info("Backfill Comment Chunks Job Starting")

    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")

    start_time = time.time()

    try:
        # Step 1: Fetch comments with context
        logger.info("Fetching comments with context...")
        comments = fetch_comments_with_context()
        logger.info("Found %d comments", len(comments))

        if not comments:
            print("\nNo comments found in database")
            return

        # Step 2: Transform to chunk records
        chunk_records = transform_to_chunk_records(comments, logger)

        if not chunk_records:
            print("\nNo valid chunk records could be created")
            return

        # Step 3: Upsert chunks
        if args.dry_run:
            results = {'total': len(chunk_records), 'upserted': len(chunk_records), 'errors': []}
            logger.info("DRY RUN: Would upsert %d chunks", len(chunk_records))
        else:
            logger.info("Upserting %d chunks...", len(chunk_records))
            results = upsert_comment_chunks(chunk_records, batch_size=args.batch_size)

        # Print summary
        elapsed_time = time.time() - start_time
        print_results_summary(results, elapsed_time, args.dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Backfill job failed: %s", e)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
