"""
CTEC-related table database operations.

All Supabase operations for instructors, course_offerings, comments, ratings, etc.
"""

from typing import Dict, List, Optional
from ..supabase_client import supabase
from .batch_helpers import batch_upsert, batch_update, create_lookup_map


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