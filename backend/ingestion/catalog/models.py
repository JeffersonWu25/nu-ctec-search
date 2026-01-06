from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re


class Department(BaseModel):
    code: str = Field(..., description="Normalized department code (e.g., 'COMP_SCI')")
    name: str = Field(..., description="Full department name")
    catalog_url: str = Field(..., description="URL to department's course catalog")
    
    @validator('code')
    def normalize_code(cls, v):
        return v.upper().replace(' ', '_').replace('-', '_')


class Course(BaseModel):
    course_code: str = Field(..., description="Full normalized course code (e.g., 'ANTHRO_275-0')")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    prerequisites_text: Optional[str] = Field(None, description="Prerequisites text or None")
    requirements: List[str] = Field(default_factory=list, description="List of distribution requirements")
    
    @validator('course_code')
    def validate_course_code(cls, v):
        # Validate format: DEPT_NUMBER-SUFFIX
        if not re.match(r'^[A-Z_]+_\d{3}-[A-Z0-9]+$', v):
            raise ValueError(f"Invalid course code format: {v}")
        return v


class ScrapedCatalogData(BaseModel):
    departments: List[Department] = Field(default_factory=list)
    courses: List[Course] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            # Custom encoders if needed
        }