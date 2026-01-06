"""
Utility functions for CTEC data upload.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.supabase_client import supabase
from setup_survey_questions import setup_survey_questions
from typing import Dict, Any, Optional, List


class UploadUtils:
    def __init__(self):
        """Initialize upload utilities with survey question mapping."""
        self.survey_mapping = setup_survey_questions()
    
    def get_or_create_course(self, course_code: str, course_title: str) -> dict:
        """
        Get existing course or create new one.
        
        Args:
            course_code: Course code (e.g., "COMP_SCI_111-0")
            course_title: Course title (e.g., "Fund Comp Prog")
            
        Returns:
            Course record with id, code, and title
        """
        if not course_code or not course_title:
            raise ValueError("Course code and title cannot be empty")
        
        # Check if course already exists
        result = supabase.table("courses").select("*").eq("code", course_code).execute()
        
        if result.data:
            course = result.data[0]
            # Update title if it's different
            if course["title"] != course_title:
                update_result = supabase.table("courses").update({
                    "title": course_title
                }).eq("id", course["id"]).execute()
                course = update_result.data[0]
                print(f"✓ Updated course title for {course_code}")
            return course
        
        # Create new course
        try:
            result = supabase.table("courses").insert({
                "code": course_code,
                "title": course_title
            }).execute()
            
            course = result.data[0]
            print(f"✓ Created new course: {course_code} - {course_title}")
            return course
            
        except Exception as e:
            print(f"❌ Error creating course {course_code}: {e}")
            raise
    
    def create_or_update_course_offering(self, course_id: str, instructor_id: str, 
                                       offering_data: dict) -> dict:
        """
        Create new course offering or update existing one.
        
        Args:
            course_id: UUID of the course
            instructor_id: UUID of the instructor
            offering_data: Dict with quarter, year, section, audience_size, response_count
            
        Returns:
            Course offering record
        """
        offering_insert = {
            "course_id": course_id,
            "instructor_id": instructor_id,
            "quarter": offering_data["quarter"],
            "year": offering_data["year"],
            "section": offering_data.get("section"),
            "audience_size": offering_data.get("audience_size"),
            "response_count": offering_data.get("response_count")
        }
        
        # Try to insert (will fail if constraint violation)
        try:
            result = supabase.table("course_offerings").insert(offering_insert).execute()
            offering = result.data[0]
            print(f"✓ Created new course offering")
            return offering
            
        except Exception as e:
            # If constraint violation, update existing offering
            if "duplicate key value violates unique constraint" in str(e).lower():
                print("✓ Course offering exists, updating...")
                
                # Find existing offering
                existing = (supabase.table("course_offerings")
                           .select("*")
                           .eq("course_id", course_id)
                           .eq("instructor_id", instructor_id)
                           .eq("quarter", offering_data["quarter"])
                           .eq("year", offering_data["year"])
                           .eq("section", offering_data.get("section"))
                           .execute())
                
                if not existing.data:
                    raise Exception("Could not find existing course offering to update")
                
                existing_id = existing.data[0]["id"]
                
                # Update the existing offering
                update_result = supabase.table("course_offerings").update({
                    "audience_size": offering_data.get("audience_size"),
                    "response_count": offering_data.get("response_count")
                }).eq("id", existing_id).execute()
                
                return update_result.data[0]
            else:
                print(f"❌ Error creating course offering: {e}")
                raise
    
    def clear_existing_offering_data(self, offering_id: str):
        """
        Clear existing comments and ratings for a course offering.
        Used when updating an existing offering.
        
        Args:
            offering_id: UUID of the course offering
        """
        try:
            # Delete existing comments
            supabase.table("comments").delete().eq("course_offering_id", offering_id).execute()
            
            # Delete existing ratings and their distributions
            # First get all rating IDs for this offering
            ratings_result = (supabase.table("ratings")
                            .select("id")
                            .eq("course_offering_id", offering_id)
                            .execute())
            
            if ratings_result.data:
                rating_ids = [r["id"] for r in ratings_result.data]
                
                # Delete rating distributions
                for rating_id in rating_ids:
                    supabase.table("ratings_distribution").delete().eq("rating_id", rating_id).execute()
                
                # Delete ratings
                supabase.table("ratings").delete().eq("course_offering_id", offering_id).execute()
            
            print(f"✓ Cleared existing data for offering {offering_id}")
            
        except Exception as e:
            print(f"❌ Error clearing existing data: {e}")
            raise
    
    def insert_comments(self, offering_id: str, comments: List[dict]) -> List[str]:
        """
        Insert comments for a course offering.
        
        Args:
            offering_id: UUID of the course offering
            comments: List of comment dicts with 'content' field
            
        Returns:
            List of inserted comment IDs
        """
        if not comments:
            return []
        
        comment_inserts = []
        for comment in comments:
            if comment.get("content") and comment["content"].strip():
                comment_inserts.append({
                    "course_offering_id": offering_id,
                    "content": comment["content"].strip()
                })
        
        if not comment_inserts:
            return []
        
        try:
            result = supabase.table("comments").insert(comment_inserts).execute()
            comment_ids = [comment["id"] for comment in result.data]
            print(f"✓ Inserted {len(comment_ids)} comments")
            return comment_ids
            
        except Exception as e:
            print(f"❌ Error inserting comments: {e}")
            raise
    
    def insert_survey_responses(self, offering_id: str, survey_responses: dict):
        """
        Insert survey responses and their distributions.
        
        Args:
            offering_id: UUID of the course offering
            survey_responses: Dict of question -> response counts
        """
        for question_text, response_data in survey_responses.items():
            if question_text not in self.survey_mapping:
                print(f"⚠ Warning: Unknown survey question: {question_text}")
                continue
            
            question_info = self.survey_mapping[question_text]
            question_id = question_info["question_id"]
            
            # Create rating record
            try:
                rating_result = supabase.table("ratings").insert({
                    "course_offering_id": offering_id,
                    "survey_question_id": question_id
                }).execute()
                
                rating_id = rating_result.data[0]["id"]
                
                # Insert response distributions
                distribution_inserts = []
                for response_label, count in response_data.items():
                    if str(response_label) in question_info["options"] and count > 0:
                        option_id = question_info["options"][str(response_label)]
                        distribution_inserts.append({
                            "rating_id": rating_id,
                            "option_id": option_id,
                            "count": count
                        })
                
                if distribution_inserts:
                    supabase.table("ratings_distribution").insert(distribution_inserts).execute()
                    print(f"✓ Inserted {len(distribution_inserts)} response distributions for: {question_text[:50]}...")
                
            except Exception as e:
                print(f"❌ Error inserting survey responses for {question_text}: {e}")
                raise
    
    def validate_ctec_record(self, ctec_data: dict) -> bool:
        """
        Validate that a CTEC record has required fields.
        
        Args:
            ctec_data: CTEC data dict
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["course", "instructor", "course_offering"]
        
        for field in required_fields:
            if field not in ctec_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate course
        course = ctec_data["course"]
        if not course.get("code") or not course.get("title"):
            print("❌ Course missing code or title")
            return False
        
        # Validate instructor
        instructor = ctec_data["instructor"]
        if not instructor.get("name"):
            print("❌ Instructor missing name")
            return False
        
        # Validate offering
        offering = ctec_data["course_offering"]
        required_offering_fields = ["quarter", "year"]
        for field in required_offering_fields:
            if field not in offering:
                print(f"❌ Course offering missing required field: {field}")
                return False
        
        return True