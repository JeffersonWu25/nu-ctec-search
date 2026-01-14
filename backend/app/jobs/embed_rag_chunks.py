#!/usr/bin/env python3
"""
Embed RAG Chunks Job - Generate embeddings for rag_chunks.

Finds chunks in rag_chunks without embeddings in rag_embeddings and
generates them using OpenAI's API.

Usage:
    python -m app.jobs.embed_rag_chunks [--dry-run] [--batch-size N] [--limit N]
"""

import sys
import argparse
import time
from typing import Dict, List, Any

from ..db.unified_rag import (
    fetch_rag_chunks_without_embeddings,
    insert_rag_embeddings
)
from ..rag.embeddings import generate_embeddings, EMBEDDING_MODEL
from ..utils.logging import get_job_logger


def process_chunks_in_batches(
    chunks: List[Dict[str, Any]],
    batch_size: int,
    dry_run: bool,
    logger
) -> Dict[str, Any]:
    """
    Generate embeddings for rag_chunks in batches.

    Args:
        chunks: List of chunk dicts with 'id' and 'content'
        batch_size: Number of chunks per API call
        dry_run: If True, skip actual API calls
        logger: Logger instance

    Returns:
        Results dict with counts and errors
    """
    results = {
        'total': len(chunks),
        'embedded': 0,
        'inserted': 0,
        'errors': []
    }

    if not chunks:
        return results

    total_batches = (len(chunks) + batch_size - 1) // batch_size
    logger.info("Processing %d chunks in %d batches", len(chunks), total_batches)

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        logger.info("Batch %d/%d (%d chunks)", batch_num, total_batches, len(batch))

        if dry_run:
            results['embedded'] += len(batch)
            results['inserted'] += len(batch)
            continue

        try:
            # Generate embeddings via OpenAI
            texts = [chunk['content'] for chunk in batch]
            embeddings = generate_embeddings(texts)
            results['embedded'] += len(embeddings)

            # Prepare records for insert into rag_embeddings
            embedding_records = [
                {
                    'chunk_id': batch[j]['id'],
                    'embedding': embeddings[j],
                    'model': EMBEDDING_MODEL
                }
                for j in range(len(batch))
            ]

            # Insert into database
            insert_result = insert_rag_embeddings(embedding_records, batch_size=batch_size)
            results['inserted'] += insert_result['inserted']

            if insert_result['errors']:
                results['errors'].extend(insert_result['errors'])

            logger.info(
                "Batch %d: embedded %d, inserted %d",
                batch_num, len(embeddings), insert_result['inserted']
            )

        except Exception as e:
            error_msg = f"Batch {batch_num}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

    return results


def print_results_summary(results: Dict[str, Any], elapsed_time: float, dry_run: bool):
    """Print job results summary."""
    print("\n" + "=" * 60)
    print("EMBED RAG CHUNKS RESULTS")
    print("=" * 60)

    print("\nSummary:")
    print(f"  Total chunks: {results['total']}")
    print(f"  Embedded: {results['embedded']}")
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
        print("\nDRY RUN completed - no API calls or DB changes made")


def main():
    """Main entry point for embed rag chunks job."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for rag_chunks into rag_embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.embed_rag_chunks                  # Embed all unembedded chunks
  python -m app.jobs.embed_rag_chunks --dry-run        # Preview without API calls
  python -m app.jobs.embed_rag_chunks --limit 100      # Embed first 100 chunks
  python -m app.jobs.embed_rag_chunks --batch-size 50  # Use smaller batches
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without API calls or DB modifications'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of chunks per API call (default: 100)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of chunks to process (default: all)'
    )

    args = parser.parse_args()

    logger = get_job_logger('embed_rag_chunks')
    logger.info("Embed RAG Chunks Job Starting")

    if args.dry_run:
        logger.info("DRY RUN MODE - no API calls or DB changes")

    start_time = time.time()

    try:
        # Step 1: Fetch rag_chunks without embeddings
        logger.info("Fetching rag_chunks without embeddings...")
        chunks = fetch_rag_chunks_without_embeddings(limit=args.limit)
        logger.info("Found %d chunks to embed", len(chunks))

        if not chunks:
            print("\nNo rag_chunks need embeddings")
            return

        # Step 2: Process in batches
        results = process_chunks_in_batches(
            chunks,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            logger=logger
        )

        # Print summary
        elapsed_time = time.time() - start_time
        print_results_summary(results, elapsed_time, args.dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Embed job failed: %s", e)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
