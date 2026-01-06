from typing import List, Optional
import json
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .models import ScrapedCatalogData, Department, Course
from .department_scraper import DepartmentScraper
from .course_scraper import CourseScraper


class CatalogScraper:
    """Main orchestrator for scraping Northwestern course catalog."""
    
    def __init__(self, 
                 delay_seconds: float = 0.5,
                 max_workers: int = 3,
                 output_dir: str = "scraped_data"):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Thread-safe data collection
        self._lock = threading.Lock()
        self._scraped_data = ScrapedCatalogData()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def scrape_all(self, 
                   limit_departments: Optional[int] = None,
                   department_filter: Optional[List[str]] = None) -> ScrapedCatalogData:
        """
        Scrape all departments and courses from Northwestern catalog.
        
        Args:
            limit_departments: Limit number of departments to scrape (for testing)
            department_filter: Only scrape specific departments by name
        """
        self.logger.info("Starting Northwestern course catalog scrape")
        
        try:
            # Step 1: Scrape departments
            departments = self._scrape_departments()
            self.logger.info(f"Found {len(departments)} departments")
            
            # Apply filters
            if department_filter:
                departments = [d for d in departments if d.name in department_filter]
                self.logger.info(f"Filtered to {len(departments)} departments")
            
            if limit_departments:
                departments = departments[:limit_departments]
                self.logger.info(f"Limited to {len(departments)} departments")
            
            # Step 2: Scrape courses for each department
            self._scrape_courses_parallel(departments)
            
            self.logger.info(f"Scraping complete. Found {len(self._scraped_data.courses)} courses")
            
            return self._scraped_data
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            raise
    
    def _scrape_departments(self) -> List[Department]:
        """Scrape all departments from the main catalog page."""
        self.logger.info("Scraping departments...")
        
        with DepartmentScraper(self.delay_seconds) as dept_scraper:
            departments = dept_scraper.scrape_departments()
        
        with self._lock:
            self._scraped_data.departments = departments
        
        # Save intermediate results
        self._save_intermediate_data("departments.json", departments)
        
        return departments
    
    def _scrape_courses_parallel(self, departments: List[Department]):
        """Scrape courses for all departments in parallel."""
        self.logger.info(f"Scraping courses for {len(departments)} departments...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all department scraping tasks
            future_to_dept = {
                executor.submit(self._scrape_single_department, dept): dept 
                for dept in departments
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_dept):
                dept = future_to_dept[future]
                try:
                    courses = future.result()
                    
                    with self._lock:
                        self._scraped_data.courses.extend(courses)
                    
                    completed += 1
                    self.logger.info(f"Completed {dept.name} ({completed}/{len(departments)}): "
                                   f"{len(courses)} courses")
                    
                    # Save incremental progress
                    if completed % 5 == 0:  # Save every 5 departments
                        self._save_intermediate_data(
                            f"courses_progress_{completed}.json", 
                            self._scraped_data.courses
                        )
                        
                except Exception as e:
                    self.logger.error(f"Failed to scrape {dept.name}: {str(e)}")
    
    def _scrape_single_department(self, department: Department) -> List[Course]:
        """Scrape courses for a single department."""
        try:
            with CourseScraper(self.delay_seconds) as course_scraper:
                courses = course_scraper.scrape_department_courses(department)
            return courses
            
        except Exception as e:
            self.logger.error(f"Error scraping {department.name}: {str(e)}")
            return []
    
    def save_to_json(self, filename: str = "catalog_data.json") -> Path:
        """Save scraped data to JSON file."""
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self._scraped_data.model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            
            self.logger.info(f"Saved data to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save data: {str(e)}")
            raise
    
    def _save_intermediate_data(self, filename: str, data):
        """Save intermediate data for debugging/recovery."""
        try:
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                if hasattr(data, 'model_dump'):
                    json.dump(data.model_dump(), f, indent=2, ensure_ascii=False)
                elif isinstance(data, list) and data and hasattr(data[0], 'model_dump'):
                    json.dump([item.model_dump() for item in data], f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.warning(f"Failed to save intermediate data to {filename}: {str(e)}")
    
    def get_stats(self) -> dict:
        """Get scraping statistics."""
        return {
            "departments_count": len(self._scraped_data.departments),
            "courses_count": len(self._scraped_data.courses),
            "departments_with_courses": len(set(c.department_code for c in self._scraped_data.courses)),
            "sample_departments": [d.name for d in self._scraped_data.departments[:5]],
            "sample_courses": [f"{c.code}: {c.title}" for c in self._scraped_data.courses[:5]]
        }