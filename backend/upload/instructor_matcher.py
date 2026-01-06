"""
Fuzzy matching module for instructor names.
Handles name normalization and matching to avoid duplicate instructors.
"""

import re
from difflib import SequenceMatcher
from typing import List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.supabase_client import supabase


class InstructorMatcher:
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the instructor matcher.
        
        Args:
            similarity_threshold: Minimum similarity score to consider a match (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self._instructor_cache = {}
        self._load_existing_instructors()
    
    def _load_existing_instructors(self):
        """Load all existing instructors from database into cache."""
        try:
            result = supabase.table("instructors").select("id, name").execute()
            self._instructor_cache = {
                self._normalize_name(instructor["name"]): instructor 
                for instructor in result.data
            }
            print(f"Loaded {len(self._instructor_cache)} existing instructors into cache")
        except Exception as e:
            print(f"Warning: Could not load existing instructors: {e}")
            self._instructor_cache = {}
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize instructor name for better matching.
        
        Args:
            name: Raw instructor name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Basic cleaning
        name = name.strip()
        
        # Remove common titles and suffixes
        titles = [
            r'\bDr\.?\s*', r'\bProf\.?\s*', r'\bProfessor\s*', 
            r'\bMr\.?\s*', r'\bMs\.?\s*', r'\bMrs\.?\s*',
            r'\s+Jr\.?$', r'\s+Sr\.?$', r'\s+III?$', r'\s+IV$'
        ]
        
        for title in titles:
            name = re.sub(title, '', name, flags=re.IGNORECASE)
        
        # Normalize whitespace and case
        name = ' '.join(name.split()).title()
        
        return name
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two normalized names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    
    def find_best_match(self, target_name: str) -> Optional[Tuple[str, dict, float]]:
        """
        Find the best matching instructor from existing instructors.
        
        Args:
            target_name: Name to match against
            
        Returns:
            Tuple of (matched_name, instructor_data, similarity_score) or None if no match
        """
        normalized_target = self._normalize_name(target_name)
        
        if not normalized_target:
            return None
        
        # Check for exact match first
        if normalized_target in self._instructor_cache:
            return (normalized_target, self._instructor_cache[normalized_target], 1.0)
        
        # Find best fuzzy match
        best_match = None
        best_score = 0.0
        
        for cached_name, instructor_data in self._instructor_cache.items():
            score = self._calculate_similarity(normalized_target, cached_name)
            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = (cached_name, instructor_data, score)
        
        return best_match
    
    def get_or_create_instructor(self, name: str) -> dict:
        """
        Get existing instructor or create new one if no match found.
        
        Args:
            name: Instructor name from CTEC data
            
        Returns:
            Instructor record with id and name
        """
        if not name or not name.strip():
            raise ValueError("Instructor name cannot be empty")
        
        # Try to find existing match
        match = self.find_best_match(name)
        
        if match:
            matched_name, instructor_data, score = match
            print(f"✓ Matched '{name}' to existing '{instructor_data['name']}' (similarity: {score:.2f})")
            return instructor_data
        
        # No match found, create new instructor
        normalized_name = self._normalize_name(name)
        
        try:
            result = supabase.table("instructors").insert({
                "name": normalized_name
            }).execute()
            
            new_instructor = result.data[0]
            print(f"✓ Created new instructor: '{normalized_name}'")
            
            # Add to cache for future matches
            self._instructor_cache[normalized_name] = new_instructor
            
            return new_instructor
            
        except Exception as e:
            print(f"❌ Error creating instructor '{name}': {e}")
            raise
    
    def refresh_cache(self):
        """Refresh the instructor cache from database."""
        self._load_existing_instructors()


def test_instructor_matching():
    """Test the instructor matching functionality."""
    matcher = InstructorMatcher()
    
    test_cases = [
        "Dr. John Smith",
        "Prof. Jane Doe",
        "Connor Bain",
        "Smith, John",
        "Jane M. Doe",
    ]
    
    print("Testing instructor matching:")
    for name in test_cases:
        try:
            instructor = matcher.get_or_create_instructor(name)
            print(f"  '{name}' -> {instructor['name']} (ID: {instructor['id']})")
        except Exception as e:
            print(f"  '{name}' -> ERROR: {e}")


if __name__ == "__main__":
    test_instructor_matching()