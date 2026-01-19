#!/usr/bin/env python3
"""
Populate RAG tables with comment embeddings.

Creates rag_chunks and rag_embeddings records for student comments.
Supports incremental updates - only processes comments not already in rag_chunks.
Supports repair mode - fixes orphaned chunks (chunks without embeddings).

Usage:
    python -m app.jobs.populate_comment_embeddings [--dry-run] [--batch-size N] [--limit N]
    python -m app.jobs.populate_comment_embeddings --repair [--dry-run]
"""

import sys
import argparse
import time
from typing import List, Dict

from ..core.openai_client import get_openai_client
from ..db.rag import (
    get_existing_comment_chunk_ids,
    get_comments_with_offering_data,
    get_chunks_without_embeddings,
    insert_rag_chunk,
    insert_rag_embedding,
    delete_chunk,
    get_rag_stats
)
from ..utils.logging import get_job_logger

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def generate_embedding_single(text: str, client) -> List[float]:
    """
    Generate embedding for a single text using OpenAI.

    Args:
        text: Text string to embed
        client: OpenAI client instance

    Returns:
        Embedding vector

    Raises:
        Exception on API failure
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text]
    )
    return response.data[0].embedding


def generate_embeddings(texts: List[str], client) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using OpenAI.

    Args:
        texts: List of text strings to embed
        client: OpenAI client instance

    Returns:
        List of embedding vectors
    """
    logger = get_job_logger('populate_comment_embeddings')

    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )

        # Sort by index to maintain order
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [e.embedding for e in embeddings]

    except Exception as e:
        logger.error("Failed to generate embeddings: %s", e)
        raise


def repair_orphaned_chunks(dry_run: bool = False) -> Dict:
    """
    Find and repair chunks that don't have embeddings.

    For each orphaned chunk:
    1. Try to generate an embedding
    2. If successful, insert the embedding
    3. If failed, delete the orphaned chunk

    Args:
        dry_run: If True, don't make any changes

    Returns:
        Dict with repair statistics
    """
    logger = get_job_logger('populate_comment_embeddings')

    results = {
        'orphaned_found': 0,
        'repaired': 0,
        'deleted': 0,
        'failed': 0,
        'errors': []
    }

    # Step 1: Find orphaned chunks
    print("\n" + "=" * 60)
    print(" REPAIR MODE: Finding orphaned chunks")
    print("=" * 60)

    orphaned_chunks = get_chunks_without_embeddings()
    results['orphaned_found'] = len(orphaned_chunks)

    if not orphaned_chunks:
        print("\n No orphaned chunks found. All chunks have embeddings.")
        return results

    print(f"\n Found {len(orphaned_chunks)} orphaned chunk(s) without embeddings:")
    print("-" * 60)

    for i, chunk in enumerate(orphaned_chunks, 1):
        content_preview = chunk['content'][:80] + "..." if len(chunk['content']) > 80 else chunk['content']
        print(f"  {i}. Chunk ID: {chunk['id'][:8]}...")
        print(f"     Entity: {chunk['entity_type']} ({chunk['entity_id'][:8]}...)")
        print(f"     Content: \"{content_preview}\"")
        print()

    if dry_run:
        print(" DRY RUN: Would attempt to repair these chunks")
        print("          Run without --dry-run to actually repair")
        return results

    # Step 2: Initialize OpenAI client
    print(" Initializing OpenAI client...")
    try:
        client = get_openai_client()
    except Exception as e:
        error_msg = f"Failed to initialize OpenAI client: {e}"
        print(f"\n ERROR: {error_msg}")
        print("        Cannot proceed with repair without OpenAI access.")
        results['errors'].append(error_msg)
        results['failed'] = len(orphaned_chunks)
        return results

    # Step 3: Attempt to repair each chunk
    print("\n Attempting to repair orphaned chunks...")
    print("-" * 60)

    for i, chunk in enumerate(orphaned_chunks, 1):
        chunk_id = chunk['id']
        entity_id = chunk['entity_id']
        content = chunk['content']

        print(f"\n [{i}/{len(orphaned_chunks)}] Processing chunk {chunk_id[:8]}...")

        # Try to generate embedding
        try:
            print(f"     Generating embedding...")
            embedding = generate_embedding_single(content, client)
            print(f"     Embedding generated ({len(embedding)} dimensions)")

        except Exception as e:
            error_msg = f"Embedding generation failed for chunk {chunk_id}: {e}"
            logger.error(error_msg)
            print(f"     FAILED: Could not generate embedding")
            print(f"     Error: {e}")

            # Delete the orphaned chunk since we can't create an embedding for it
            print(f"     Deleting orphaned chunk...")
            if delete_chunk(chunk_id):
                print(f"     DELETED: Orphaned chunk removed from database")
                results['deleted'] += 1
            else:
                print(f"     ERROR: Could not delete orphaned chunk!")
                print(f"            Manual intervention required for chunk {chunk_id}")
                results['failed'] += 1
                results['errors'].append(f"Could not delete orphaned chunk {chunk_id}")

            continue

        # Try to insert embedding
        try:
            print(f"     Inserting embedding into rag_embeddings...")
            embedding_result = insert_rag_embedding(
                chunk_id=chunk_id,
                embedding=embedding,
                model=EMBEDDING_MODEL
            )

            if embedding_result:
                print(f"     REPAIRED: Embedding successfully added")
                results['repaired'] += 1
            else:
                raise Exception("insert_rag_embedding returned None")

        except Exception as e:
            error_msg = f"Embedding insertion failed for chunk {chunk_id}: {e}"
            logger.error(error_msg)
            print(f"     FAILED: Could not insert embedding")
            print(f"     Error: {e}")

            # Delete the orphaned chunk since we can't save the embedding
            print(f"     Deleting orphaned chunk...")
            if delete_chunk(chunk_id):
                print(f"     DELETED: Orphaned chunk removed from database")
                results['deleted'] += 1
            else:
                print(f"     ERROR: Could not delete orphaned chunk!")
                print(f"            Manual intervention required for chunk {chunk_id}")
                results['failed'] += 1
                results['errors'].append(f"Could not delete orphaned chunk {chunk_id}")

    return results


def process_comments_batch(
    comments: List[Dict],
    client,
    dry_run: bool = False
) -> Dict:
    """
    Process a batch of comments: create chunks and embeddings.

    Args:
        comments: List of comment dicts with metadata
        client: OpenAI client instance
        dry_run: If True, don't actually insert data

    Returns:
        Dict with success/failure counts
    """
    logger = get_job_logger('populate_comment_embeddings')

    results = {
        'chunks_created': 0,
        'embeddings_created': 0,
        'failed': 0,
        'errors': []
    }

    if not comments:
        return results

    if dry_run:
        logger.info("DRY RUN: Would process %d comments", len(comments))
        results['chunks_created'] = len(comments)
        results['embeddings_created'] = len(comments)
        return results

    # Step 1: Generate embeddings for all comments in batch
    texts = [c['content'] for c in comments]

    try:
        embeddings = generate_embeddings(texts, client)
    except Exception as e:
        error_msg = f"Batch embedding generation failed: {e}"
        logger.error(error_msg)
        results['failed'] = len(comments)
        results['errors'].append(error_msg)
        return results

    # Step 2: Insert chunks and embeddings one by one
    for i, comment in enumerate(comments):
        try:
            # Insert chunk
            chunk = insert_rag_chunk(
                entity_type='comment',
                entity_id=comment['id'],
                content=comment['content'],
                chunk_type='student_comment',
                course_id=comment.get('course_id'),
                instructor_id=comment.get('instructor_id'),
                course_offering_id=comment.get('course_offering_id'),
                chunk_index=0
            )

            if not chunk:
                error_msg = f"Failed to insert chunk for comment {comment['id']}"
                logger.error(error_msg)
                results['failed'] += 1
                results['errors'].append(error_msg)
                continue

            results['chunks_created'] += 1

            # Insert embedding
            embedding_result = insert_rag_embedding(
                chunk_id=chunk['id'],
                embedding=embeddings[i],
                model=EMBEDDING_MODEL
            )

            if embedding_result:
                results['embeddings_created'] += 1
            else:
                error_msg = f"Failed to insert embedding for chunk {chunk['id']} (comment {comment['id']})"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                # Note: This creates an orphaned chunk - use --repair to fix

        except Exception as e:
            error_msg = f"Error processing comment {comment['id']}: {e}"
            logger.error(error_msg)
            results['failed'] += 1
            results['errors'].append(error_msg)

    return results


def estimate_cost(comment_count: int) -> float:
    """
    Estimate OpenAI API cost for embedding generation.

    text-embedding-3-small: $0.00002 per 1K tokens
    Average comment ~50 tokens

    Args:
        comment_count: Number of comments to process

    Returns:
        Estimated cost in USD
    """
    avg_tokens_per_comment = 50
    total_tokens = comment_count * avg_tokens_per_comment
    cost_per_1k_tokens = 0.00002
    return (total_tokens / 1000) * cost_per_1k_tokens


def print_final_stats():
    """Print final RAG table statistics."""
    stats = get_rag_stats()
    print(f"\n RAG Table Stats:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Total embeddings: {stats['total_embeddings']}")
    print(f"   Comment chunks: {stats['comment_chunks']}")

    # Check for orphaned chunks
    orphan_count = stats['total_chunks'] - stats['total_embeddings']
    if orphan_count > 0:
        print(f"\n WARNING: {orphan_count} orphaned chunk(s) detected!")
        print(f"          Run with --repair to fix orphaned chunks.")
    elif stats['total_chunks'] > 0:
        print(f"\n All chunks have embeddings.")


def run_populate_mode(args):
    """Run the normal populate mode."""
    logger = get_job_logger('populate_comment_embeddings')

    print("\n" + "=" * 60)
    print(" POPULATE MODE: Adding new comment embeddings")
    print("=" * 60)

    # Step 1: Get existing comment IDs in rag_chunks
    print("\n Checking existing RAG chunks...")
    existing_ids = get_existing_comment_chunk_ids()
    print(f"   Found {len(existing_ids)} comments already in rag_chunks")

    # Step 2: Get comments that need processing
    print("\n Fetching comments from database...")
    all_comments = get_comments_with_offering_data(
        limit=args.limit,
        exclude_ids=existing_ids
    )

    # Filter out already processed (in case limit was used)
    comments_to_process = [c for c in all_comments if c['id'] not in existing_ids]

    if args.limit:
        comments_to_process = comments_to_process[:args.limit]

    total_to_process = len(comments_to_process)

    if total_to_process == 0:
        print("\n All comments already have chunks. Nothing to do.")
        print("   (Run with --repair to check for orphaned chunks)")
        return

    # Step 3: Estimate cost
    estimated_cost = estimate_cost(total_to_process)
    print(f"\n Found {total_to_process} new comment(s) to process")
    print(f"   Estimated cost: ${estimated_cost:.4f}")

    if args.max_cost and estimated_cost > args.max_cost:
        print(f"\n ERROR: Estimated cost ${estimated_cost:.4f} exceeds limit ${args.max_cost:.4f}")
        print("        Use --limit to reduce scope or increase --max-cost")
        sys.exit(1)

    if args.dry_run:
        print(f"\n DRY RUN: Would process {total_to_process} comments")
        print(f"          Batch size: {args.batch_size}")
        print(f"          Number of batches: {(total_to_process + args.batch_size - 1) // args.batch_size}")
        return

    # Step 4: Initialize OpenAI client
    print("\n Initializing OpenAI client...")
    try:
        client = get_openai_client()
    except Exception as e:
        print(f"\n ERROR: Failed to initialize OpenAI client: {e}")
        print("        Check that OPENAI_API_KEY is set correctly.")
        sys.exit(1)

    # Step 5: Process in batches
    print(f"\n Processing {total_to_process} comments in batches of {args.batch_size}...")
    print("-" * 60)

    total_results = {
        'chunks_created': 0,
        'embeddings_created': 0,
        'failed': 0,
        'errors': []
    }

    num_batches = (total_to_process + args.batch_size - 1) // args.batch_size

    for batch_num in range(num_batches):
        batch_start = batch_num * args.batch_size
        batch_end = min(batch_start + args.batch_size, total_to_process)
        batch = comments_to_process[batch_start:batch_end]

        logger.info(
            "[Batch %d/%d] Processing comments %d-%d",
            batch_num + 1, num_batches, batch_start + 1, batch_end
        )

        batch_results = process_comments_batch(batch, client, dry_run=False)

        # Accumulate results
        total_results['chunks_created'] += batch_results['chunks_created']
        total_results['embeddings_created'] += batch_results['embeddings_created']
        total_results['failed'] += batch_results['failed']
        total_results['errors'].extend(batch_results['errors'])

        # Progress update
        processed = batch_end
        success_rate = batch_results['embeddings_created'] / len(batch) * 100 if batch else 0
        print(
            f"   Batch {batch_num + 1}/{num_batches}: "
            f"{batch_results['embeddings_created']}/{len(batch)} successful "
            f"({success_rate:.0f}%) | "
            f"Total: {processed}/{total_to_process}"
        )

        # Small delay between batches to be nice to the API
        if batch_num < num_batches - 1:
            time.sleep(0.5)

    # Step 6: Print results
    print("\n" + "=" * 60)
    print(" RESULTS")
    print("=" * 60)
    print(f"   Chunks created: {total_results['chunks_created']}")
    print(f"   Embeddings created: {total_results['embeddings_created']}")
    print(f"   Failed: {total_results['failed']}")

    # Check for mismatches (orphaned chunks created)
    orphans_created = total_results['chunks_created'] - total_results['embeddings_created']
    if orphans_created > 0:
        print(f"\n WARNING: {orphans_created} chunk(s) created without embeddings!")
        print(f"          Run with --repair to fix these orphaned chunks.")

    if total_results['errors']:
        print(f"\n Errors encountered ({len(total_results['errors'])}):")
        for error in total_results['errors'][:5]:
            print(f"   - {error}")
        if len(total_results['errors']) > 5:
            print(f"   ... and {len(total_results['errors']) - 5} more")


def run_repair_mode(args):
    """Run the repair mode to fix orphaned chunks."""
    results = repair_orphaned_chunks(dry_run=args.dry_run)

    if args.dry_run:
        return

    # Print repair results
    print("\n" + "=" * 60)
    print(" REPAIR RESULTS")
    print("=" * 60)
    print(f"   Orphaned chunks found: {results['orphaned_found']}")
    print(f"   Successfully repaired: {results['repaired']}")
    print(f"   Deleted (unrepairable): {results['deleted']}")
    print(f"   Failed: {results['failed']}")

    if results['failed'] > 0:
        print(f"\n ERROR: {results['failed']} chunk(s) could not be repaired or deleted!")
        print("        Manual intervention may be required.")
        print("        Check the errors below:")
        for error in results['errors']:
            print(f"        - {error}")

    if results['repaired'] > 0:
        print(f"\n Successfully repaired {results['repaired']} chunk(s).")

    if results['deleted'] > 0:
        print(f"\n Deleted {results['deleted']} unrepairable chunk(s).")
        print("   These comments will be re-processed on the next normal run.")


def main():
    """Main entry point for comment embedding population job."""
    parser = argparse.ArgumentParser(
        description="Populate RAG tables with comment embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.populate_comment_embeddings                    # Process all new comments
  python -m app.jobs.populate_comment_embeddings --dry-run          # Preview without changes
  python -m app.jobs.populate_comment_embeddings --batch-size 50    # Smaller batches
  python -m app.jobs.populate_comment_embeddings --limit 100        # Process only 100 comments
  python -m app.jobs.populate_comment_embeddings --repair           # Fix orphaned chunks
  python -m app.jobs.populate_comment_embeddings --repair --dry-run # Preview repair
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without calling OpenAI or updating database'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of comments to embed per API call (default: 100)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum total comments to process'
    )
    parser.add_argument(
        '--max-cost',
        type=float,
        help='Maximum estimated cost in USD'
    )
    parser.add_argument(
        '--repair',
        action='store_true',
        help='Repair mode: fix orphaned chunks (chunks without embeddings)'
    )

    args = parser.parse_args()

    logger = get_job_logger('populate_comment_embeddings')
    logger.info("=" * 60)
    logger.info("Comment Embedding Job Starting")
    logger.info("Mode: %s", "REPAIR" if args.repair else "POPULATE")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        if args.repair:
            run_repair_mode(args)
        else:
            run_populate_mode(args)

        # Print final stats
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
