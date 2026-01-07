#!/usr/bin/env python3
"""
Upload departments from scraped catalog data to Supabase departments table.
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from api.supabase_client import supabase


def load_departments_data(file_path: str) -> List[Dict]:
    """Load departments data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} departments from {file_path}")
        return data
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        print("Run 'python scrape_departments.py' first to generate the data")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def upload_departments(departments: List[Dict], batch_size: int = 100) -> Dict:
    """Upload departments to Supabase using batch upserts."""
    print(f"Uploading {len(departments)} departments in batches of {batch_size}")
    
    results = {
        "total": len(departments),
        "uploaded": 0,
        "errors": []
    }
    
    # Process in batches
    for i in range(0, len(departments), batch_size):
        batch = departments[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(departments) + batch_size - 1) // batch_size
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} departments)")
        
        try:
            # Upsert batch to departments table
            response = supabase.table('departments').upsert(
                batch,
                on_conflict='code'  # Use code as the conflict resolution key
            ).execute()
            
            uploaded_count = len(response.data) if response.data else len(batch)
            results["uploaded"] += uploaded_count
            
            print(f"  ✅ Uploaded {uploaded_count} departments")
            
        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            results["errors"].append(error_msg)
    
    return results


def print_summary(results: Dict):
    """Print upload summary."""
    print("\n" + "=" * 50)
    print("📊 UPLOAD SUMMARY")
    print("=" * 50)
    print(f"Total departments: {results['total']}")
    print(f"Successfully uploaded: {results['uploaded']}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    success_rate = (results['uploaded'] / results['total']) * 100 if results['total'] > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")


def main():
    """Main upload function."""
    print("🏫 Department Uploader")
    print("=" * 30)
    
    # Default path to departments mapping file
    departments_file = Path(__file__).parent.parent / "scraped_data" / "departments_mapping.json"
    
    # Check if custom file path provided
    if len(sys.argv) > 1:
        departments_file = Path(sys.argv[1])
    
    print(f"Loading departments from: {departments_file}")
    
    # Load departments data
    departments_data = load_departments_data(str(departments_file))
    
    # Validate data structure
    if not departments_data or not isinstance(departments_data, list):
        print("❌ Invalid data structure. Expected a list of departments.")
        sys.exit(1)
    
    # Check first item has required fields
    if not departments_data[0].get('code') or not departments_data[0].get('name'):
        print("❌ Invalid department format. Expected 'code' and 'name' fields.")
        sys.exit(1)
    
    # Show sample data
    print(f"\nSample departments:")
    for i, dept in enumerate(departments_data[:5], 1):
        print(f"  {i}. {dept['name']} ({dept['code']})")
    
    if len(departments_data) > 5:
        print(f"  ... and {len(departments_data) - 5} more")
    
    # Confirm upload
    confirm = input(f"\nUpload {len(departments_data)} departments to database? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Upload cancelled.")
        return
    
    # Upload departments
    try:
        results = upload_departments(departments_data)
        print_summary(results)
        
        if results['uploaded'] == results['total']:
            print("\n🎉 All departments uploaded successfully!")
        else:
            print(f"\n⚠️  {results['total'] - results['uploaded']} departments failed to upload.")
            
    except Exception as e:
        print(f"\n❌ Upload failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()