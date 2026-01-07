#!/usr/bin/env python3
"""
Extract department names and codes from Northwestern course catalog.
"""

import json
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))


def scrape_departments():
    """Extract department names and codes from the catalog page."""
    url = "https://catalogs.northwestern.edu/undergraduate/courses-az/"
    
    print(f"Scraping departments from: {url}")
    
    # Make request
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Pattern to match department names: "Department Name (DEPT_CODE)"
    department_pattern = re.compile(r'^.+\s*\([A-Z][A-Z_&]+\)$')
    
    # Extract department info
    departments = []
    seen_codes = set()  # Avoid duplicates
    
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        text = link.get_text(strip=True)
        
        # Check if text matches department pattern and targets undergraduate courses
        if (department_pattern.match(text) and 
            href and '/undergraduate/courses-az/' in href and 
            not href.endswith('.pdf')):
            
            # Extract department name and code
            dept_info = extract_department_info(text)
            if dept_info and dept_info['code'] not in seen_codes:
                departments.append(dept_info)
                seen_codes.add(dept_info['code'])
    
    print(f"Found {len(departments)} unique departments")
    return departments


def extract_department_info(text):
    """Extract department name and code from text like 'Chemistry (CHEM)'."""
    # Pattern to capture: "Department Name (CODE)"
    match = re.match(r'^(.+?)\s*\(([A-Z][A-Z_&]+)\)$', text.strip())
    
    if match:
        name = match.group(1).strip()
        code = match.group(2).strip()
        
        return {
            'code': code,
            'name': name
        }
    
    return None


def save_departments_json(departments, output_dir="scraped_data"):
    """Save departments to JSON file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "departments_mapping.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(departments, f, indent=2, ensure_ascii=False)
    
    print(f"Departments saved to: {output_file}")
    return output_file


def main():
    """Main function to scrape and save departments."""
    try:
        print("🏫 Northwestern Departments Scraper")
        print("=" * 40)
        
        # Scrape departments
        departments = scrape_departments()
        
        # Save to JSON
        output_file = save_departments_json(departments)
        
        # Print sample results
        print(f"\nSample departments:")
        for i, dept in enumerate(departments[:10], 1):
            print(f"{i:2d}. {dept['name']} ({dept['code']})")
        
        if len(departments) > 10:
            print(f"... and {len(departments) - 10} more")
        
        print(f"\n✅ Complete! All departments saved to {output_file}")
        
    except Exception as e:
        print(f"\n❌ Failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()