"""
Course metrics database operations.

Handles aggregation of ratings across course offerings and upserting to course_metrics table.
"""

from typing import Dict, List, Optional
from ..supabase_client import supabase


# Exact survey question text -> course_metrics column name mapping
# These must match the question text in the survey_questions table exactly
SURVEY_QUESTION_MAP = {
    "Provide an overall rating of the instruction": "instruction_rating_avg",
    "Provide an overall rating of the course": "course_rating_avg",
    "Estimate how much you learned in the course": "learned_avg",
    "Rate the effectiveness of the course in challenging you intellectually": "intellectually_challenging_avg",
    "Rate the effectiveness of the instructor in stimulating your interest in the subject": "instructor_interest_avg",
    "What was your Interest in this subject before taking the course?": "prior_interest_avg",
}

# The hours per week question (handled separately as mode, not average)
HOURS_QUESTION_TEXT = "Estimate the average number of hours per week you spent on this course outside of class and lab time"


def get_all_course_ids() -> List[str]:
    """
    Get all course IDs from the database.

    Returns:
        List of course UUID strings
    """
    try:
        response = supabase.table('courses').select('id').execute()
        return [row['id'] for row in response.data]
    except Exception as e:
        print(f"Failed to fetch course IDs: {e}")
        return []


def get_survey_question_id_map() -> Dict[str, str]:
    """
    Get mapping of question text -> question ID for the questions we care about.

    Returns:
        Dictionary mapping question text to question UUID
    """
    try:
        response = supabase.table('survey_questions').select('id, question').execute()
        return {row['question']: row['id'] for row in response.data}
    except Exception as e:
        print(f"Failed to fetch survey questions: {e}")
        return {}


def compute_course_rating_averages(course_id: str, question_id: str) -> Optional[float]:
    """
    Compute weighted average rating for a course across all its offerings for a specific question.

    Formula: sum(count * numeric_value) / sum(count) across all offerings

    Args:
        course_id: UUID of the course
        question_id: UUID of the survey question

    Returns:
        Weighted average as float, or None if no data
    """
    try:
        # Get all course_offerings for this course
        offerings_response = supabase.table('course_offerings').select('id').eq('course_id', course_id).execute()

        if not offerings_response.data:
            return None

        offering_ids = [o['id'] for o in offerings_response.data]

        total_weighted_sum = 0.0
        total_count = 0

        for offering_id in offering_ids:
            # Get rating for this offering and question
            rating_response = supabase.table('ratings').select('id').eq(
                'course_offering_id', offering_id
            ).eq(
                'survey_question_id', question_id
            ).execute()

            if not rating_response.data:
                continue

            rating_id = rating_response.data[0]['id']

            # Get distribution for this rating with option numeric values
            dist_response = supabase.table('ratings_distribution').select(
                'count, option_id'
            ).eq('rating_id', rating_id).execute()

            if not dist_response.data:
                continue

            # Get numeric values for each option
            for dist in dist_response.data:
                option_response = supabase.table('survey_question_options').select(
                    'numeric_value'
                ).eq('id', dist['option_id']).execute()

                if option_response.data and option_response.data[0]['numeric_value'] is not None:
                    numeric_value = option_response.data[0]['numeric_value']
                    count = dist['count']
                    total_weighted_sum += count * numeric_value
                    total_count += count

        if total_count == 0:
            return None

        return round(total_weighted_sum / total_count, 2)

    except Exception as e:
        print(f"Failed to compute rating average for course {course_id}, question {question_id}: {e}")
        return None


def compute_course_hours_mode(course_id: str, hours_question_id: str) -> Optional[str]:
    """
    Compute the mode (most common bucket) for hours per week across all offerings.

    Args:
        course_id: UUID of the course
        hours_question_id: UUID of the hours survey question

    Returns:
        Label of the most common hours bucket (e.g., "4 - 7"), or None if no data
    """
    try:
        # Get all course_offerings for this course
        offerings_response = supabase.table('course_offerings').select('id').eq('course_id', course_id).execute()

        if not offerings_response.data:
            return None

        offering_ids = [o['id'] for o in offerings_response.data]

        # Aggregate counts per bucket label across all offerings
        bucket_counts: Dict[str, int] = {}

        for offering_id in offering_ids:
            # Get rating for this offering and the hours question
            rating_response = supabase.table('ratings').select('id').eq(
                'course_offering_id', offering_id
            ).eq(
                'survey_question_id', hours_question_id
            ).execute()

            if not rating_response.data:
                continue

            rating_id = rating_response.data[0]['id']

            # Get distribution for this rating
            dist_response = supabase.table('ratings_distribution').select(
                'count, option_id'
            ).eq('rating_id', rating_id).execute()

            if not dist_response.data:
                continue

            # Get labels and aggregate counts
            for dist in dist_response.data:
                option_response = supabase.table('survey_question_options').select(
                    'label'
                ).eq('id', dist['option_id']).execute()

                if option_response.data:
                    label = option_response.data[0]['label']
                    bucket_counts[label] = bucket_counts.get(label, 0) + dist['count']

        if not bucket_counts:
            return None

        # Find the mode (bucket with highest count)
        mode_label = max(bucket_counts, key=bucket_counts.get)
        return mode_label

    except Exception as e:
        print(f"Failed to compute hours mode for course {course_id}: {e}")
        return None


def compute_metrics_for_course(course_id: str, question_id_map: Dict[str, str]) -> Optional[Dict]:
    """
    Compute all metrics for a single course.

    Args:
        course_id: UUID of the course
        question_id_map: Mapping of question text -> question UUID

    Returns:
        Dictionary with all metric fields, or None if course has no data
    """
    metrics = {
        'course_id': course_id,
        'learned_avg': None,
        'course_rating_avg': None,
        'instructor_interest_avg': None,
        'prior_interest_avg': None,
        'intellectually_challenging_avg': None,
        'instruction_rating_avg': None,
        'hours_per_week_mode': None,
    }

    has_any_data = False

    # Compute averages for each rating question
    for question_text, column_name in SURVEY_QUESTION_MAP.items():
        question_id = question_id_map.get(question_text)
        if question_id:
            avg_value = compute_course_rating_averages(course_id, question_id)
            if avg_value is not None:
                metrics[column_name] = avg_value
                has_any_data = True

    # Compute hours mode
    hours_question_id = question_id_map.get(HOURS_QUESTION_TEXT)
    if hours_question_id:
        hours_mode = compute_course_hours_mode(course_id, hours_question_id)
        if hours_mode is not None:
            metrics['hours_per_week_mode'] = hours_mode
            has_any_data = True

    return metrics if has_any_data else None


def upsert_course_metrics(metrics_list: List[Dict]) -> Dict:
    """
    Upsert course metrics in batches.

    Args:
        metrics_list: List of metrics records

    Returns:
        Dictionary with results: {'total', 'upserted', 'errors'}
    """
    results = {
        'total': len(metrics_list),
        'upserted': 0,
        'errors': []
    }

    if not metrics_list:
        return results

    batch_size = 100

    for i in range(0, len(metrics_list), batch_size):
        batch = metrics_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(metrics_list) + batch_size - 1) // batch_size

        try:
            response = supabase.table('course_metrics').upsert(
                batch,
                on_conflict='course_id'
            ).execute()

            upserted_count = len(response.data) if response.data else len(batch)
            results['upserted'] += upserted_count
            print(f"   Batch {batch_num}/{total_batches}: upserted {upserted_count} records")

        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"   {error_msg}")
            results['errors'].append(error_msg)

    return results


def get_course_metrics_stats() -> Dict:
    """
    Get statistics about the course_metrics table.

    Returns:
        Dictionary with counts and stats
    """
    try:
        response = supabase.table('course_metrics').select('*', count='exact').execute()

        total = response.count if response.count is not None else len(response.data)

        # Count non-null fields
        with_course_rating = sum(1 for r in response.data if r.get('course_rating_avg') is not None)
        with_instruction_rating = sum(1 for r in response.data if r.get('instruction_rating_avg') is not None)
        with_hours = sum(1 for r in response.data if r.get('hours_per_week_mode') is not None)

        return {
            'total_records': total,
            'with_course_rating': with_course_rating,
            'with_instruction_rating': with_instruction_rating,
            'with_hours_mode': with_hours,
        }
    except Exception as e:
        print(f"Failed to get course_metrics stats: {e}")
        return {'total_records': 0}
