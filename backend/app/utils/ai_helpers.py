"""
AI helper utilities for text chunking and summary generation.

Provides utilities for processing text for AI summarization tasks.
"""

import re
import time
import random
from typing import List, Dict, Any

from ..core.openai_client import get_openai_client
from ..core.prompts import get_prompt


def chunk_text(text: str, max_chunk_size: int = 2000, overlap_size: int = 200) -> List[str]:
    """
    Split text into overlapping chunks suitable for LLM processing.

    Args:
        text: Text to chunk
        max_chunk_size: Maximum characters per chunk
        overlap_size: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Find the end of this chunk
        end = start + max_chunk_size

        if end >= len(text):
            # Last chunk
            chunks.append(text[start:])
            break

        # Try to break at a sentence boundary within the last 100 characters
        break_point = end
        search_start = max(start, end - 100)

        # Look for sentence endings
        for match in re.finditer(r'[.!?]\s+', text[search_start:end]):
            break_point = search_start + match.end()

        chunks.append(text[start:break_point])

        # Next chunk starts with overlap
        start = max(start + 1, break_point - overlap_size)

    return chunks


def chunk_comments_by_offering(comments_data: List[Dict]) -> List[str]:
    """
    Group and chunk comments by offering context.

    Args:
        comments_data: List of comment dicts with offering context

    Returns:
        List of text chunks with offering context
    """
    # Group comments by offering
    offering_groups = {}
    for comment in comments_data:
        offering_id = comment['course_offering_id']
        if offering_id not in offering_groups:
            offering = comment['course_offerings']
            course = offering['courses']
            course_quarter = f"{offering['quarter']} {offering['year']}"
            context = f"{course['code']} - {course['title']} ({course_quarter})"
            offering_groups[offering_id] = {
                'context': context,
                'comments': []
            }
        offering_groups[offering_id]['comments'].append(comment['content'])

    # Create chunks for each offering
    chunks = []
    for offering_id, group in offering_groups.items():
        context = group['context']
        comments_text = '\n\n'.join(group['comments'])

        # Chunk the comments for this offering (leave room for context)
        comment_chunks = chunk_text(comments_text, max_chunk_size=1800)

        for i, chunk in enumerate(comment_chunks):
            if len(comment_chunks) > 1:
                chunk_header = f"=== {context} (Part {i+1}/{len(comment_chunks)}) ===\n\n"
            else:
                chunk_header = f"=== {context} ===\n\n"

            chunks.append(chunk_header + chunk)

    return chunks


def generate_ai_summary(
    entity_type: str,
    content: List[str],
    model: str = "gpt-4o-mini",
    max_retries: int = 3
) -> str:
    """
    Generate AI summary using OpenAI API with retry logic.

    Args:
        entity_type: Type of entity ('course_offering', 'instructor', 'course')
        content: List of comments or summaries to analyze
        model: OpenAI model to use
        max_retries: Maximum number of retry attempts

    Returns:
        Generated summary text

    Raises:
        Exception: If OpenAI API call fails after all retries
    """
    if not content:
        return f"No data available for {entity_type} summary."

    # Prepare content text based on entity type and validate size
    if entity_type == 'course_offering':
        content_text = '\n\n---\n\n'.join(content)
    elif entity_type == 'instructor':
        content_text = '\n\n'.join(content)  # content is already chunked
    elif entity_type == 'course':
        content_text = '\n\n---\n\n'.join(content)
    else:
        content_text = '\n\n'.join(content)
    
    # Truncate if too large (rough estimate: ~4 chars per token)
    max_input_chars = 12000  # ~3000 tokens, leave room for prompts and output
    if len(content_text) > max_input_chars:
        content_text = content_text[:max_input_chars] + "...\n[Content truncated]"

    # Get prompts from centralized prompt file
    system_prompt, user_prompt = get_prompt(entity_type, content_text)

    # Call OpenAI API with retry logic
    client = get_openai_client()
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=1000,  # Reasonable limit for summaries
            )

            summary = response.choices[0].message.content.strip()

            if not summary:
                raise Exception("OpenAI returned empty response")

            return summary

        except Exception as e:
            last_exception = e
            
            # Check if it's a retryable error
            error_str = str(e).lower()
            if any(code in error_str for code in ['429', 'rate limit', 'server error', '5']):
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    continue
            
            # Non-retryable error or max retries exceeded
            break
    
    raise Exception(f"Failed to generate {entity_type} summary after {max_retries + 1} attempts: {str(last_exception)}")


def prepare_instructor_content(comments_data: List[Dict]) -> List[str]:
    """
    Prepare instructor comment data for summarization.

    Args:
        comments_data: List of comment dicts with offering context

    Returns:
        List of formatted content strings
    """
    return chunk_comments_by_offering(comments_data)


def validate_summary(summary: str, min_length: int = 100, max_length: int = 2000) -> Dict[str, Any]:
    """
    Validate generated summary meets basic quality criteria.

    Args:
        summary: Generated summary text
        min_length: Minimum acceptable length
        max_length: Maximum acceptable length

    Returns:
        Dict with validation results
    """
    issues = []

    if len(summary) < min_length:
        issues.append(f"Summary too short ({len(summary)} chars, minimum {min_length})")

    if len(summary) > max_length:
        issues.append(f"Summary too long ({len(summary)} chars, maximum {max_length})")

    # Check for hallucination indicators
    hallucination_indicators = [
        "based on my knowledge",
        "i recommend",
        "in my experience",
        "typically",
        "usually",
        "generally speaking"
    ]

    summary_lower = summary.lower()
    for indicator in hallucination_indicators:
        if indicator in summary_lower:
            issues.append(f"Potential hallucination detected: '{indicator}'")

    # Check for empty content
    empty_responses = ['', 'No summary available.', 'Unable to generate summary.']
    if summary.strip() in empty_responses:
        issues.append("Empty or placeholder summary")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'length': len(summary),
        'word_count': len(summary.split())
    }


def format_staleness_report(stale_data: Dict[str, List[Dict]]) -> str:
    """Format staleness detection results for display."""
    report_lines = []

    report_lines.append("🔍 AI SUMMARY STALENESS REPORT")
    report_lines.append("=" * 50)

    for entity_type, entities in stale_data.items():
        if not entities:
            continue

        entity_title = entity_type.replace('_', ' ').title()
        report_lines.append(f"\n📊 {entity_title}s ({len(entities)} stale):")

        for i, entity in enumerate(entities[:10]):  # Show first 10
            if entity_type == 'course_offering':
                offering_id = entity['course_offering_id'][:8]
                comment_date = entity['latest_comment_at'][:10]
                line = f"  {i+1}. Offering {offering_id}... (latest comment: {comment_date})"
                report_lines.append(line)
            elif entity_type == 'instructor':
                instructor_id = entity['instructor_id'][:8]
                latest_comment = entity['latest_comment_at'][:10]
                line = f"  {i+1}. Instructor {instructor_id}... (latest comment: {latest_comment})"
                report_lines.append(line)
            elif entity_type == 'course':
                course_id = entity['course_id'][:8]
                latest_summary = entity['latest_offering_summary_at'][:10]
                line = f"  {i+1}. Course {course_id}... (latest offering summary: {latest_summary})"
                report_lines.append(line)

        if len(entities) > 10:
            report_lines.append(f"  ... and {len(entities) - 10} more")

    total_stale = sum(len(entities) for entities in stale_data.values())
    report_lines.append(f"\n📈 Total entities needing updates: {total_stale}")

    return '\n'.join(report_lines)


def estimate_cost(entity_counts: Dict[str, int], model: str = "gpt-4o-mini") -> float:
    """
    Estimate cost for AI summary generation.
    
    Args:
        entity_counts: Dict with entity_type -> count
        model: OpenAI model name
    
    Returns:
        Estimated cost in USD
    """
    # Rough cost estimates per entity (including input + output tokens)
    costs_per_entity = {
        "gpt-4o-mini": {
            'course_offering': 0.005,  # ~1000 input tokens + 500 output tokens
            'instructor': 0.015,       # ~3000 input tokens + 500 output tokens  
            'course': 0.008           # ~1500 input tokens + 500 output tokens
        },
        "gpt-4o": {
            'course_offering': 0.03,
            'instructor': 0.08,
            'course': 0.05
        }
    }
    
    model_costs = costs_per_entity.get(model, costs_per_entity["gpt-4o-mini"])
    
    total_cost = 0.0
    for entity_type, count in entity_counts.items():
        entity_cost = model_costs.get(entity_type, 0.01)  # Default fallback
        total_cost += count * entity_cost
    
    return total_cost


def apply_entity_limits(stale_data: Dict[str, List[Dict]], max_entities: int) -> Dict[str, List[Dict]]:
    """
    Apply entity count limits across all types proportionally.
    
    Args:
        stale_data: Dict with entity_type -> list of entities
        max_entities: Maximum total entities to process
        
    Returns:
        Limited stale_data dict
    """
    total_entities = sum(len(entities) for entities in stale_data.values())
    
    if total_entities <= max_entities:
        return stale_data
    
    # Calculate proportional limits
    limited_data = {}
    entities_allocated = 0
    
    for entity_type, entities in stale_data.items():
        if not entities:
            limited_data[entity_type] = []
            continue
            
        # Calculate proportional share
        proportion = len(entities) / total_entities
        type_limit = max(1, int(max_entities * proportion))  # At least 1 if any exist
        
        # Don't exceed remaining budget
        remaining = max_entities - entities_allocated
        actual_limit = min(type_limit, remaining, len(entities))
        
        limited_data[entity_type] = entities[:actual_limit]
        entities_allocated += actual_limit
        
        if entities_allocated >= max_entities:
            break
    
    return limited_data
