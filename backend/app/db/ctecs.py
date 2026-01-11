"""
CTEC-related table database operations.

All Supabase operations for instructors, course_offerings, comments, ratings, etc.
"""

from typing import Dict, List, Optional
from ..supabase_client import supabase
from .batch_helpers import batch_upsert, create_lookup_map


# Instructors Table Operations

def get_all_instructors() -> List[Dict]:
    """
    Get all instructors from the database.
    
    Returns:
        List of instructor records with id, name
    """
    try:
        response = supabase.table('instructors').select('*').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch instructors: {e}")
        return []


def get_instructors_lookup() -> Dict[str, str]:
    """
    Get instructors as lookup map: name -> id.
    
    Returns:
        Dictionary mapping instructor name to instructor id
    """
    return create_lookup_map('instructors', 'name', 'id')


def get_instructor_by_name(name: str) -> Optional[Dict]:
    """
    Get a single instructor by name.
    
    Args:
        name: Instructor name
        
    Returns:
        Instructor record or None if not found
    """
    try:
        response = supabase.table('instructors').select('*').eq('name', name).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to fetch instructor {name}: {e}")
        return None


def upsert_instructors(instructors: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert instructors in batches.
    
    Args:
        instructors: List of instructor records with 'name' field
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='instructors',
        data=instructors,
        conflict_key='name',
        batch_size=batch_size,
        description='instructors'
    )


# Course Offerings Table Operations

def get_all_course_offerings() -> List[Dict]:
    """
    Get all course offerings from the database.
    
    Returns:
        List of course offering records
    """
    try:
        response = supabase.table('course_offerings').select('*').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch course offerings: {e}")
        return []


def get_course_offering_by_details(course_id: str, instructor_id: str, quarter: str, year: int, section: Optional[int] = None) -> Optional[Dict]:
    """
    Get a course offering by its identifying details.
    
    Args:
        course_id: UUID of the course
        instructor_id: UUID of the instructor
        quarter: Quarter (Fall, Winter, Spring, Summer)
        year: Year (e.g., 2023)
        section: Optional section number
        
    Returns:
        Course offering record or None if not found
    """
    try:
        query = supabase.table('course_offerings').select('*').eq('course_id', course_id).eq('instructor_id', instructor_id).eq('quarter', quarter).eq('year', year)
        
        if section is not None:
            query = query.eq('section', section)
        else:
            query = query.is_('section', 'null')
            
        response = query.execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Failed to fetch course offering: {e}")
        return None


def upsert_course_offerings(course_offerings: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert course offerings in batches.
    
    Args:
        course_offerings: List of course offering records
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='course_offerings',
        data=course_offerings,
        conflict_key='course_id,instructor_id,quarter,year,section',
        batch_size=batch_size,
        description='course offerings'
    )


def upsert_course_offering_returning_id(offering_data: Dict) -> Optional[str]:
    """
    Upsert a single course offering and return its ID.
    
    Implements the upsert-returning pattern to reliably get the offering ID
    without race conditions.
    
    Args:
        offering_data: Course offering record with required fields
        
    Returns:
        UUID string of the course offering ID, or None if operation failed
    """
    try:
        response = supabase.table('course_offerings').upsert(
            offering_data,
            on_conflict='course_id,instructor_id,quarter,year,section'
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        else:
            print(f"❌ Failed to get offering ID after upsert")
            return None
            
    except Exception as e:
        print(f"❌ Failed to upsert course offering: {e}")
        return None


def clear_offering_snapshot_data(course_offering_id: str) -> Dict:
    """
    Delete all snapshot data (comments, ratings, and rating_distributions) for a course offering.
    
    This implements the "replace snapshot" policy for CTEC uploads:
    - Comments are deleted directly
    - Ratings are deleted (rating_distributions cascade automatically)
    - Rating_distributions are also explicitly deleted for safety
    
    Used before inserting fresh CTEC data to ensure clean replacement
    of all offering-scoped data when the same CTEC is uploaded multiple times.
    
    Args:
        course_offering_id: UUID of the course offering to clear
        
    Returns:
        Dictionary with deletion results: {'comments_deleted', 'ratings_deleted', 'distributions_deleted', 'errors'}
    """
    results = {
        'comments_deleted': 0,
        'ratings_deleted': 0,
        'distributions_deleted': 0,
        'errors': []
    }
    
    try:
        # First, get counts before deletion for accurate reporting
        comments_before = len(get_comments_by_offering(course_offering_id))
        ratings_before = len(get_ratings_by_offering(course_offering_id))
        
        # Get distribution count before deletion (via ratings)
        distributions_before = 0
        ratings = get_ratings_by_offering(course_offering_id)
        for rating in ratings:
            distributions_before += len(get_rating_distributions(rating['id']))
        
        # Delete rating distributions first (to avoid foreign key issues)
        for rating in ratings:
            supabase.table('ratings_distribution').delete().eq(
                'rating_id', rating['id']
            ).execute()
        
        # Delete comments for this offering
        supabase.table('comments').delete().eq(
            'course_offering_id', course_offering_id
        ).execute()
        
        # Delete ratings for this offering
        supabase.table('ratings').delete().eq(
            'course_offering_id', course_offering_id
        ).execute()
        
        # Use the counts we obtained before deletion
        results['comments_deleted'] = comments_before
        results['ratings_deleted'] = ratings_before
        results['distributions_deleted'] = distributions_before
        
        print(f"🗑️  Cleared snapshot data for offering {course_offering_id}: "
              f"{results['comments_deleted']} comments, {results['ratings_deleted']} ratings, "
              f"{results['distributions_deleted']} distributions")
        
        # Brief pause to ensure database consistency
        import time
        time.sleep(0.1)
        
    except Exception as e:
        error_msg = f"Failed to clear snapshot data for offering {course_offering_id}: {e}"
        print(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results


# Survey Questions Table Operations

def get_all_survey_questions() -> List[Dict]:
    """
    Get all survey questions from the database.
    
    Returns:
        List of survey question records
    """
    try:
        response = supabase.table('survey_questions').select('*').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch survey questions: {e}")
        return []


def get_survey_questions_lookup() -> Dict[str, str]:
    """
    Get survey questions as lookup map: question -> id.
    
    Returns:
        Dictionary mapping question text to question id
    """
    return create_lookup_map('survey_questions', 'question', 'id')


def upsert_survey_questions(questions: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert survey questions in batches.
    
    Args:
        questions: List of question records with 'question' field
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='survey_questions',
        data=questions,
        conflict_key='question',
        batch_size=batch_size,
        description='survey questions'
    )


# Comments Table Operations

def get_comments_by_offering(course_offering_id: str) -> List[Dict]:
    """
    Get all comments for a specific course offering.
    
    Args:
        course_offering_id: UUID of the course offering
        
    Returns:
        List of comment records
    """
    try:
        response = supabase.table('comments').select('*').eq('course_offering_id', course_offering_id).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch comments for offering {course_offering_id}: {e}")
        return []


def upsert_comments(comments: List[Dict], batch_size: int = 500) -> Dict:
    """
    Upsert comments in batches.
    
    Args:
        comments: List of comment records with course_offering_id, content, content_hash
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='comments',
        data=comments,
        conflict_key='course_offering_id,content_hash',
        batch_size=batch_size,
        description='comments'
    )


def insert_comments(comments: List[Dict], batch_size: int = 500) -> Dict:
    """
    Insert comments in batches (for snapshot replacement - no conflict resolution).
    
    Used in the "replace snapshot" model where comments are pre-cleared
    and we need clean insertion without upsert logic.
    
    Args:
        comments: List of comment records with course_offering_id, content, content_hash
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with insert results: {'total', 'inserted', 'errors'}
    """
    results = {
        'total': len(comments),
        'inserted': 0,
        'errors': []
    }
    
    if not comments:
        return results
    
    print(f"📝 Inserting {len(comments)} comments in batches of {batch_size}")
    
    for i in range(0, len(comments), batch_size):
        batch = comments[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(comments) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} comments)")
        
        try:
            response = supabase.table('comments').insert(batch).execute()
            inserted_count = len(response.data) if response.data else len(batch)
            results['inserted'] += inserted_count
            print(f"   ✅ Inserted {inserted_count} comments")
            
        except Exception as e:
            error_msg = f"Comment batch {batch_num} failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
    
    return results


# Ratings Table Operations

def get_ratings_by_offering(course_offering_id: str) -> List[Dict]:
    """
    Get all ratings for a specific course offering.
    
    Args:
        course_offering_id: UUID of the course offering
        
    Returns:
        List of rating records
    """
    try:
        response = supabase.table('ratings').select('*').eq('course_offering_id', course_offering_id).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch ratings for offering {course_offering_id}: {e}")
        return []


def upsert_ratings(ratings: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert ratings in batches.
    
    Args:
        ratings: List of rating records with course_offering_id, survey_question_id
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='ratings',
        data=ratings,
        conflict_key='course_offering_id,survey_question_id',
        batch_size=batch_size,
        description='ratings'
    )


def insert_ratings(ratings: List[Dict], batch_size: int = 100) -> Dict:
    """
    Insert ratings in batches (for snapshot replacement - no conflict resolution).
    
    Used in the "replace snapshot" model where ratings are pre-cleared
    and we need clean insertion without upsert logic.
    
    Args:
        ratings: List of rating records with course_offering_id, survey_question_id
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with insert results: {'total', 'inserted', 'errors'}
    """
    results = {
        'total': len(ratings),
        'inserted': 0,
        'errors': []
    }
    
    if not ratings:
        return results
    
    print(f"📊 Inserting {len(ratings)} ratings in batches of {batch_size}")
    
    for i in range(0, len(ratings), batch_size):
        batch = ratings[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(ratings) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} ratings)")
        
        try:
            response = supabase.table('ratings').insert(batch).execute()
            inserted_count = len(response.data) if response.data else len(batch)
            results['inserted'] += inserted_count
            print(f"   ✅ Inserted {inserted_count} ratings")
            
        except Exception as e:
            error_msg = f"Rating batch {batch_num} failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
    
    return results


# Survey Question Options Table Operations

def get_survey_question_options(survey_question_id: str) -> List[Dict]:
    """
    Get all options for a specific survey question.
    
    Args:
        survey_question_id: UUID of the survey question
        
    Returns:
        List of option records
    """
    try:
        response = supabase.table('survey_question_options').select('*').eq('survey_question_id', survey_question_id).order('ordinal').execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch options for question {survey_question_id}: {e}")
        return []


def upsert_survey_question_options(options: List[Dict], batch_size: int = 100) -> Dict:
    """
    Upsert survey question options in batches.
    
    Args:
        options: List of option records
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='survey_question_options',
        data=options,
        conflict_key='survey_question_id,label',
        batch_size=batch_size,
        description='survey question options'
    )


# Ratings Distribution Table Operations

def get_rating_distributions(rating_id: str) -> List[Dict]:
    """
    Get distribution data for a specific rating.
    
    Args:
        rating_id: UUID of the rating
        
    Returns:
        List of distribution records
    """
    try:
        response = supabase.table('ratings_distribution').select('*').eq('rating_id', rating_id).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch distributions for rating {rating_id}: {e}")
        return []


def upsert_rating_distributions(distributions: List[Dict], batch_size: int = 500) -> Dict:
    """
    Upsert rating distributions in batches.
    
    Args:
        distributions: List of distribution records with rating_id, option_id, count
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with upload results: {'total', 'uploaded', 'errors'}
    """
    return batch_upsert(
        table_name='ratings_distribution',
        data=distributions,
        conflict_key='rating_id,option_id',
        batch_size=batch_size,
        description='rating distributions'
    )


def insert_rating_distributions(distributions: List[Dict], batch_size: int = 500) -> Dict:
    """
    Insert rating distributions in batches (for snapshot replacement - no conflict resolution).
    
    Used in the "replace snapshot" model where rating distributions are pre-cleared
    via cascade delete when ratings are deleted.
    
    Args:
        distributions: List of distribution records with rating_id, option_id, count
        batch_size: Number of records per batch
        
    Returns:
        Dictionary with insert results: {'total', 'inserted', 'errors'}
    """
    results = {
        'total': len(distributions),
        'inserted': 0,
        'errors': []
    }
    
    if not distributions:
        return results
    
    print(f"📈 Inserting {len(distributions)} rating distributions in batches of {batch_size}")
    
    for i in range(0, len(distributions), batch_size):
        batch = distributions[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(distributions) + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} distributions)")
        
        try:
            response = supabase.table('ratings_distribution').insert(batch).execute()
            inserted_count = len(response.data) if response.data else len(batch)
            results['inserted'] += inserted_count
            print(f"   ✅ Inserted {inserted_count} distributions")
            
        except Exception as e:
            error_msg = f"Distribution batch {batch_num} failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            results['errors'].append(error_msg)
    
    return results