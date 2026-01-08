#!/usr/bin/env python3
"""
Setup survey questions job - initialize survey questions and options in database.

Usage:
    python -m app.jobs.setup_survey_questions [--dry-run]
"""

import sys
import argparse

from ..db.ctecs import upsert_survey_questions, upsert_survey_question_options
from ..utils.logging import get_job_logger


# Standard CTEC survey questions
STANDARD_QUESTIONS = [
    "Provide an overall rating of the instruction",
    "Provide an overall rating of the course",
    "Estimate how much you learned in the course",
    "Rate the effectiveness of the course in challenging you intellectually",
    "Rate the effectiveness of the instructor in stimulating your interest in the subject",
    "What is the name of your school?",
    "Your Class",
    "What is your reason for taking the course? (mark all that apply)",
    "What was your Interest in this subject before taking the course?",
    "Estimate the average number of hours per week you spent on this course outside of class and lab time"
]

# Standard options for Likert scale questions (1-6)
LIKERT_OPTIONS = [
    {"label": "1", "ordinal": 1, "numeric_value": 1, "is_open_ended_max": False},
    {"label": "2", "ordinal": 2, "numeric_value": 2, "is_open_ended_max": False},
    {"label": "3", "ordinal": 3, "numeric_value": 3, "is_open_ended_max": False},
    {"label": "4", "ordinal": 4, "numeric_value": 4, "is_open_ended_max": False},
    {"label": "5", "ordinal": 5, "numeric_value": 5, "is_open_ended_max": False},
    {"label": "6", "ordinal": 6, "numeric_value": 6, "is_open_ended_max": False},
]

# Time range options
TIME_RANGE_OPTIONS = [
    {"label": "3 or fewer", "ordinal": 1, "max_value": 3, "is_open_ended_max": False},
    {"label": "4 - 7", "ordinal": 2, "min_value": 4, "max_value": 7, "is_open_ended_max": False},
    {"label": "8 - 11", "ordinal": 3, "min_value": 8, "max_value": 11, "is_open_ended_max": False},
    {"label": "12 - 15", "ordinal": 4, "min_value": 12, "max_value": 15, "is_open_ended_max": False},
    {"label": "16 - 19", "ordinal": 5, "min_value": 16, "max_value": 19, "is_open_ended_max": False},
    {"label": "20 or more", "ordinal": 6, "min_value": 20, "is_open_ended_max": True},
]


def main():
    """Main entry point for setup survey questions job."""
    parser = argparse.ArgumentParser(
        description="Setup survey questions and options in database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.jobs.setup_survey_questions                      # Setup all questions
  python -m app.jobs.setup_survey_questions --dry-run           # Preview what would be created
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying'
    )
    
    args = parser.parse_args()
    
    logger = get_job_logger('setup_survey_questions')
    logger.info("📋 Survey Questions Setup")
    logger.info("=" * 30)
    
    try:
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print(f"\nWould create {len(STANDARD_QUESTIONS)} survey questions:")
            for i, question in enumerate(STANDARD_QUESTIONS, 1):
                print(f"  {i}. {question}")
            print(f"\nWould create options for rating questions (6 options each)")
            print(f"Would create time range options ({len(TIME_RANGE_OPTIONS)} options)")
            print("\n✅ Setup preview completed")
            return
        
        # Create survey questions
        logger.info(f"Creating {len(STANDARD_QUESTIONS)} survey questions")
        question_data = [{'question': q} for q in STANDARD_QUESTIONS]
        
        question_results = upsert_survey_questions(question_data)
        
        if question_results.get('errors'):
            print(f"❌ Failed to create questions: {question_results['errors']}")
            sys.exit(1)
        
        print(f"✅ Created/updated {question_results.get('uploaded', 0)} survey questions")
        
        # Get question lookup to create options
        from ..db.ctecs import get_survey_questions_lookup
        questions_lookup = get_survey_questions_lookup()
        
        # Create options for Likert scale questions (1-5)
        likert_questions = STANDARD_QUESTIONS[:5]  # First 5 are Likert scale
        
        option_data = []
        for question in likert_questions:
            if question in questions_lookup:
                question_id = questions_lookup[question]
                for option in LIKERT_OPTIONS:
                    option_record = {
                        'survey_question_id': question_id,
                        **option
                    }
                    option_data.append(option_record)
        
        # Create options for time survey question
        time_question = "Estimate the average number of hours per week you spent on this course outside of class and lab time"
        if time_question in questions_lookup:
            question_id = questions_lookup[time_question]
            for option in TIME_RANGE_OPTIONS:
                option_record = {
                    'survey_question_id': question_id,
                    **option
                }
                option_data.append(option_record)
        
        if option_data:
            logger.info(f"Creating {len(option_data)} survey question options")
            option_results = upsert_survey_question_options(option_data)
            
            if option_results.get('errors'):
                print(f"⚠️  Some options failed to create: {option_results['errors']}")
            
            print(f"✅ Created/updated {option_results.get('uploaded', 0)} survey options")
        
        print("\n🎉 Survey questions setup completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()