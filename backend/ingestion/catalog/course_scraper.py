import httpx
from bs4 import BeautifulSoup, Tag
from typing import List, Optional
import time
import re
from .models import Course, Department


class CourseScraper:
    """Scrapes individual course information from Northwestern department pages."""
    
    def __init__(self, delay_seconds: float = 0.5):
        self.delay_seconds = delay_seconds
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; course-catalog-scraper/1.0)'
            }
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def scrape_department_courses(self, department: Department) -> List[Course]:
        """Scrape all courses for a given department."""
        try:
            response = self.client.get(department.catalog_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            courses = []
            
            # Find course blocks - these usually have class "courseblock" or similar
            course_blocks = self._find_course_blocks(soup)
            
            for block in course_blocks:
                course = self._parse_course_block(block, department.code)
                if course:
                    courses.append(course)
            
            # Rate limiting
            time.sleep(self.delay_seconds)
            
            return courses
            
        except Exception as e:
            raise Exception(f"Failed to scrape courses for {department.name}: {str(e)}")
    
    def _find_course_blocks(self, soup: BeautifulSoup) -> List[Tag]:
        """Find course blocks in the department page HTML."""
        # Try multiple selectors as different departments might use different structures
        selectors = [
            '.courseblock',
            '.course',
            '[class*="course"]',
            'div[data-course]',
            # Fallback: look for blocks with course numbers
            'div:has(strong):contains(".")',  # Many courses have "DEPT 123." format
        ]
        
        for selector in selectors:
            blocks = soup.select(selector)
            if blocks:
                return blocks
        
        # Ultimate fallback: manual parsing
        return self._manual_course_detection(soup)
    
    def _manual_course_detection(self, soup: BeautifulSoup) -> List[Tag]:
        """Manual detection of course blocks when standard selectors fail."""
        course_blocks = []
        
        # Look for patterns like "DEPT 123" or "DEPT 123-0"
        course_pattern = re.compile(r'\b[A-Z]{2,}\s+\d{3}(-\d)?\b')
        
        # Search through all divs and paragraphs
        for element in soup.find_all(['div', 'p']):
            text = element.get_text(strip=True)
            if course_pattern.search(text):
                course_blocks.append(element)
        
        return course_blocks
    
    def _parse_course_block(self, block: Tag, dept_code: str) -> Optional[Course]:
        """Parse a single course block to extract course information."""
        try:
            text = block.get_text(separator=' ', strip=True)
            
            # Extract course number and title
            course_match = self._extract_course_info(text)
            if not course_match:
                return None
            
            course_identifier, title = course_match
            
            # Handle the case where we got a full normalized code vs just a number
            if '_' in course_identifier:
                # Already has department - use as full code
                full_course_code = course_identifier
                course_num = course_identifier.split('_')[-1]  # Extract just the number part
            else:
                # Just a number - combine with department
                course_num = course_identifier
                full_course_code = f"{dept_code}_{course_num}"
            
            # Extract description
            description = self._extract_description(block, text)
            
            # Extract prerequisites
            prereqs = self._extract_prerequisites(text)
            
            # Extract requirements/distribution areas
            requirements = self._extract_requirements(text)
            
            return Course(
                course_code=full_course_code,  # Use the normalized full code
                title=title,
                description=description or "",  # Ensure description is not None
                prerequisites_text=prereqs,
                requirements=requirements  # Already a list
            )
            
        except Exception as e:
            # Log but don't fail the entire scrape
            print(f"Warning: Failed to parse course block: {str(e)}")
            return None
    
    def _extract_course_info(self, text: str) -> Optional[tuple[str, str]]:
        """
        Extract course number and title from Northwestern course text.
        
        Expected formats:
        - "AFST 101-7 Introduction to African Studies"
        - "AFST 360-SA Special Topics"  
        - "ART HIST 211-0 Art and Ideas"
        
        Returns normalized format: "AFST_101-7", title
        """
        # Pattern to match: DEPT_NAME NUMBER-SUFFIX TITLE
        # Examples: "AFST 101-7", "AFST 360-SA", "ART HIST 211-0"
        pattern = r'^([A-Z]+(?:\s+[A-Z&]+)*)\s+(\d{3}-(?:\d+|[A-Z]+))\s+(.+)$'
        
        match = re.search(pattern, text.strip(), re.MULTILINE)
        if match:
            dept_part, course_num, title = match.groups()
            
            # Normalize department: "ART HIST" -> "ART_HIST"
            dept_normalized = dept_part.strip().replace(' ', '_').replace('&', '_')
            
            # Create full normalized code: "ART_HIST_211-0" 
            full_course_code = f"{dept_normalized}_{course_num.strip()}"
            
            return full_course_code, title.strip()
        
        return None
    
    
    def _extract_description(self, block: Tag, text: str) -> Optional[str]:
        """Extract course description from the block."""
        # Try to find description in structured elements first
        desc_selectors = ['.description', '.course-description', 'p']
        
        for selector in desc_selectors:
            desc_elem = block.select_one(selector)
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 50:  # Reasonable description length
                    return desc_text
        
        # Fallback: extract from full text after title
        lines = text.split('\n')
        if len(lines) > 1:
            # Skip first line (likely title), take subsequent content
            description_lines = []
            for line in lines[1:]:
                line = line.strip()
                if line and not self._is_metadata_line(line):
                    description_lines.append(line)
                elif description_lines:  # Stop at first metadata after description
                    break
            
            if description_lines:
                return ' '.join(description_lines)
        
        return None
    
    def _extract_prerequisites(self, text: str) -> Optional[str]:
        """Extract prerequisites information from Northwestern course text."""
        # Look for lines starting with "Prerequisite:"
        prereq_patterns = [
            r'Prerequisite:\s*(.+?)(?:\n|$)',
            r'Prerequisites:\s*(.+?)(?:\n|$)',
            r'Prereq:\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in prereq_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                prereq_text = match.group(1).strip()
                if prereq_text and len(prereq_text) > 3:
                    return prereq_text
        
        return None
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract distribution requirements from Northwestern course text."""
        # Exact Northwestern distribution requirements
        requirement_keywords = [
            "Advanced Expression",
            "Global Perspectives on Power, Justice, and Equity", 
            "U.S. Perspectives on Power, Justice, and Equity",
            "Empirical and Deductive Reasoning Foundational Dis",
            "Formal Studies Distro Area",
            "Literature Fine Arts Distro Area", 
            "Literature and Arts Foundational Discipline",
            "Ethical and Evaluative Thinking Foundational Disci",
            "Ethics Values Distro Area",
            "Natural Sciences Distro Area",
            "Natural Sciences Foundational Discipline",
            "Social Behavioral Sciences Distro Area",
            "Social and Behavioral Science Foundational Discipl",
            "Historical Studies Distro Area",
            "Historical Studies Foundational Discipline",
            "Interdisciplinary Distro"
        ]
        
        # Look for any of these requirements in the text
        found_requirements = []
        for requirement in requirement_keywords:
            if requirement.lower() in text.lower():
                found_requirements.append(requirement)
        
        return found_requirements
    
    def _is_metadata_line(self, line: str) -> bool:
        """Check if a line contains metadata rather than description."""
        metadata_indicators = [
            'prerequisite', 'required', 'distribution', 'units', 'credit',
            'quarter', 'semester', 'instructor', 'time', 'location'
        ]
        
        line_lower = line.lower()
        return any(indicator in line_lower for indicator in metadata_indicators)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()