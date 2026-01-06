"""
Setup script to initialize survey questions and options in the database.
This script is idempotent and can be run multiple times safely.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.supabase_client import supabase


def setup_survey_questions():
    """
    Set up survey questions and their options in the database.
    Returns a mapping of question text to question info for use in CTEC uploads.
    """
    
    # Define all survey questions and their options
    survey_questions = [
        {
            "question": "Provide an overall rating of the instruction",
            "type": "likert",
            "options": [
                {"label": "1", "ordinal": 0, "numeric_value": 1},
                {"label": "2", "ordinal": 1, "numeric_value": 2},
                {"label": "3", "ordinal": 2, "numeric_value": 3},
                {"label": "4", "ordinal": 3, "numeric_value": 4},
                {"label": "5", "ordinal": 4, "numeric_value": 5},
                {"label": "6", "ordinal": 5, "numeric_value": 6},
            ]
        },
        {
            "question": "Provide an overall rating of the course",
            "type": "likert",
            "options": [
                {"label": "1", "ordinal": 0, "numeric_value": 1},
                {"label": "2", "ordinal": 1, "numeric_value": 2},
                {"label": "3", "ordinal": 2, "numeric_value": 3},
                {"label": "4", "ordinal": 3, "numeric_value": 4},
                {"label": "5", "ordinal": 4, "numeric_value": 5},
                {"label": "6", "ordinal": 5, "numeric_value": 6},
            ]
        },
        {
            "question": "Estimate how much you learned in the course",
            "type": "likert",
            "options": [
                {"label": "1", "ordinal": 0, "numeric_value": 1},
                {"label": "2", "ordinal": 1, "numeric_value": 2},
                {"label": "3", "ordinal": 2, "numeric_value": 3},
                {"label": "4", "ordinal": 3, "numeric_value": 4},
                {"label": "5", "ordinal": 4, "numeric_value": 5},
                {"label": "6", "ordinal": 5, "numeric_value": 6},
            ]
        },
        {
            "question": "Rate the effectiveness of the course in challenging you intellectually",
            "type": "likert",
            "options": [
                {"label": "1", "ordinal": 0, "numeric_value": 1},
                {"label": "2", "ordinal": 1, "numeric_value": 2},
                {"label": "3", "ordinal": 2, "numeric_value": 3},
                {"label": "4", "ordinal": 3, "numeric_value": 4},
                {"label": "5", "ordinal": 4, "numeric_value": 5},
                {"label": "6", "ordinal": 5, "numeric_value": 6},
            ]
        },
        {
            "question": "Rate the effectiveness of the instructor in stimulating your interest in the subject",
            "type": "likert",
            "options": [
                {"label": "1", "ordinal": 0, "numeric_value": 1},
                {"label": "2", "ordinal": 1, "numeric_value": 2},
                {"label": "3", "ordinal": 2, "numeric_value": 3},
                {"label": "4", "ordinal": 3, "numeric_value": 4},
                {"label": "5", "ordinal": 4, "numeric_value": 5},
                {"label": "6", "ordinal": 5, "numeric_value": 6},
            ]
        },
        {
            "question": "What was your Interest in this subject before taking the course?",
            "type": "likert",
            "options": [
                {"label": "1", "ordinal": 0, "numeric_value": 1},
                {"label": "2", "ordinal": 1, "numeric_value": 2},
                {"label": "3", "ordinal": 2, "numeric_value": 3},
                {"label": "4", "ordinal": 3, "numeric_value": 4},
                {"label": "5", "ordinal": 4, "numeric_value": 5},
                {"label": "6", "ordinal": 5, "numeric_value": 6},
            ]
        },
        {
            "question": "What is the name of your school?",
            "type": "categorical",
            "options": [
                {"label": "Education & SP", "ordinal": 0},
                {"label": "Communication", "ordinal": 1},
                {"label": "Graduate School", "ordinal": 2},
                {"label": "KGSM", "ordinal": 3},
                {"label": "McCormick", "ordinal": 4},
                {"label": "Medill", "ordinal": 5},
                {"label": "Music", "ordinal": 6},
                {"label": "Summer", "ordinal": 7},
                {"label": "SPS", "ordinal": 8},
                {"label": "WCAS", "ordinal": 9},
            ]
        },
        {
            "question": "Your Class",
            "type": "categorical",
            "options": [
                {"label": "Freshman", "ordinal": 0},
                {"label": "Sophomore", "ordinal": 1},
                {"label": "Junior", "ordinal": 2},
                {"label": "Senior", "ordinal": 3},
                {"label": "Graduate", "ordinal": 4},
                {"label": "Professional", "ordinal": 5},
                {"label": "Other", "ordinal": 6},
            ]
        },
        {
            "question": "What is your reason for taking the course? (mark all that apply)",
            "type": "categorical",
            "options": [
                {"label": "Distribution requirement", "ordinal": 0},
                {"label": "Major/Minor requirement", "ordinal": 1},
                {"label": "Elective requirement", "ordinal": 2},
                {"label": "Non-Degree requirement", "ordinal": 3},
                {"label": "No requirement", "ordinal": 4},
                {"label": "Other requirement", "ordinal": 5},
            ]
        },
        {
            "question": "Estimate the average number of hours per week you spent on this course outside of class and lab time",
            "type": "categorical",
            "options": [
                {"label": "3 or fewer", "ordinal": 0, "max_value": 3},
                {"label": "4 - 7", "ordinal": 1, "min_value": 4, "max_value": 7},
                {"label": "8 - 11", "ordinal": 2, "min_value": 8, "max_value": 11},
                {"label": "12 - 15", "ordinal": 3, "min_value": 12, "max_value": 15},
                {"label": "16 - 19", "ordinal": 4, "min_value": 16, "max_value": 19},
                {"label": "20 or more", "ordinal": 5, "min_value": 20, "is_open_ended_max": True},
            ]
        },
    ]
    
    question_mapping = {}
    
    print("Setting up survey questions and options...")
    
    for question_data in survey_questions:
        question_text = question_data["question"]
        
        # Check if question already exists
        existing_question = supabase.table("survey_questions").select("*").eq("question", question_text).execute()
        
        if existing_question.data:
            question_id = existing_question.data[0]["id"]
            print(f"✓ Question already exists: {question_text}")
        else:
            # Insert new question
            result = supabase.table("survey_questions").insert({"question": question_text}).execute()
            question_id = result.data[0]["id"]
            print(f"✓ Created question: {question_text}")
        
        # Setup options for this question
        options_mapping = {}
        
        for option_data in question_data["options"]:
            # Check if option already exists
            existing_option = (supabase.table("survey_question_options")
                              .select("*")
                              .eq("survey_question_id", question_id)
                              .eq("label", option_data["label"])
                              .execute())
            
            if existing_option.data:
                option_id = existing_option.data[0]["id"]
            else:
                # Prepare option insert data
                insert_data = {
                    "survey_question_id": question_id,
                    "label": option_data["label"],
                    "ordinal": option_data["ordinal"],
                    "is_open_ended_max": option_data.get("is_open_ended_max", False)
                }
                
                # Add optional fields if they exist
                if "numeric_value" in option_data:
                    insert_data["numeric_value"] = option_data["numeric_value"]
                if "min_value" in option_data:
                    insert_data["min_value"] = option_data["min_value"]
                if "max_value" in option_data:
                    insert_data["max_value"] = option_data["max_value"]
                
                result = supabase.table("survey_question_options").insert(insert_data).execute()
                option_id = result.data[0]["id"]
                print(f"  ✓ Created option: {option_data['label']}")
            
            options_mapping[option_data["label"]] = option_id
        
        question_mapping[question_text] = {
            "question_id": question_id,
            "options": options_mapping
        }
    
    print(f"\n✅ Setup complete! {len(survey_questions)} questions with all options ready.")
    return question_mapping


if __name__ == "__main__":
    try:
        mapping = setup_survey_questions()
        print("\n📋 Survey Question Mapping:")
        for question, info in mapping.items():
            print(f"\n{question[:60]}...")
            print(f"  Question ID: {info['question_id']}")
            print(f"  Options: {len(info['options'])} configured")
    
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)