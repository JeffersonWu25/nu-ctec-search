#!/usr/bin/env python3
"""
Temporary compatibility wrapper for update_course_departments.py

This script maintains backward compatibility during the transition to the new job system.
Use: python -m app.jobs.update_course_departments instead.
"""

import sys
from pathlib import Path

# Add backend directory to path so we can import app
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import and run the new job
from app.jobs.update_course_departments import main

if __name__ == "__main__":
    print("⚠️  COMPATIBILITY MODE")
    print("This script is deprecated. Please use:")
    print("python -m app.jobs.update_course_departments")
    print()
    
    # Run the new job
    main()