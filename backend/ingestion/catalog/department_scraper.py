import httpx
from bs4 import BeautifulSoup
from typing import List
import time
import re
from .models import Department


class DepartmentScraper:
    """Scrapes department information from Northwestern course catalog."""
    
    BASE_URL = "https://catalogs.northwestern.edu/undergraduate/courses-az"
    
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
    
    def scrape_departments(self) -> List[Department]:
        """Scrape all departments from the A-Z courses page."""
        try:
            response = self.client.get(self.BASE_URL)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            departments = []
            
            # Find main undergraduate department links  
            # Pattern: /undergraduate/courses-az/[dept]/
            dept_links = soup.find_all('a', href=re.compile(r'/undergraduate/courses-az/[^/]+/?$'))
            
            # Filter to only include links with department pattern: "Department Name (CODE)"
            filtered_links = []
            department_pattern = re.compile(r'^.+\s*\([A-Z][A-Z_&]+\)$')
            
            for link in dept_links:
                text = link.get_text(strip=True)
                if department_pattern.match(text):
                    filtered_links.append(link)
            
            dept_links = filtered_links
            
            for link in dept_links:
                href = link.get('href')
                if not href:
                    continue
                
                # Extract department info from link
                dept_name = link.get_text(strip=True)
                if not dept_name:
                    continue
                
                # Build full URL
                full_url = f"https://catalogs.northwestern.edu{href}" if href.startswith('/') else href
                
                # Extract department code from link text (it's in parentheses)
                dept_code = self._extract_department_code_from_text(dept_name, href)
                
                departments.append(Department(
                    code=dept_code,
                    name=dept_name,
                    catalog_url=full_url
                ))
                
                # Rate limiting
                time.sleep(self.delay_seconds)
            
            return departments
            
        except Exception as e:
            raise Exception(f"Failed to scrape departments: {str(e)}")
    
    def _extract_department_code_from_text(self, dept_name: str, href: str) -> str:
        """
        Extract department code from link text or URL.
        
        Northwestern link format: "Biological Sciences (BIOL_SCI)"
        URL format: "/sps/courses-az/undergraduate/biol_sci/"
        """
        # First try to extract from parentheses in link text
        paren_match = re.search(r'\(([^)]+)\)', dept_name)
        if paren_match:
            return paren_match.group(1).upper().replace('-', '_')
        
        # Fallback: extract from URL path
        url_match = re.search(r'/undergraduate/courses-az/([^/]+)/?$', href)
        if url_match:
            return url_match.group(1).upper().replace('-', '_')
        
        # Last resort: generate from department name
        return self._generate_code_from_name(dept_name)
    
    def _generate_code_from_name(self, dept_name: str) -> str:
        """Generate department code from name as fallback."""
        name_words = dept_name.upper().split()
        
        # Handle special cases
        special_mappings = {
            'COMPUTER SCIENCE': 'COMP_SCI',
            'ELECTRICAL ENGINEERING': 'ELEC_ENG',
            'MECHANICAL ENGINEERING': 'MECH_ENG',
            'BIOMEDICAL ENGINEERING': 'BIOMED_ENG',
            'MATERIALS SCIENCE': 'MAT_SCI',
            'POLITICAL SCIENCE': 'POLI_SCI',
            'AFRICAN AMERICAN STUDIES': 'AFAM',
            'ASIAN AMERICAN STUDIES': 'ASIAN_AM'
        }
        
        full_name = ' '.join(name_words)
        if full_name in special_mappings:
            return special_mappings[full_name]
        
        # Default: take first 4 chars of first word, or first 2 chars of first 2 words
        if len(name_words) == 1:
            return name_words[0][:8]  # Max 8 chars for single words
        else:
            # Take first few chars of first two words
            code_parts = []
            for word in name_words[:2]:
                if len(word) >= 4:
                    code_parts.append(word[:4])
                else:
                    code_parts.append(word)
            return '_'.join(code_parts)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()