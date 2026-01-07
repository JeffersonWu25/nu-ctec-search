#!/usr/bin/env python3
"""
End-to-end script to scrape Northwestern departments and upload to database.

This script:
1. Scrapes department names and codes from Northwestern catalog
2. Uploads them to the Supabase departments table
3. Handles the entire workflow in one command
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

import scrape_departments
from upload.upload_departments import upload_departments


def main():
    """Run the complete department scraping and upload workflow."""
    print("🏫 Northwestern Departments - Complete Workflow")
    print("=" * 55)
    
    try:
        # Step 1: Scrape departments
        print("STEP 1: Scraping departments from Northwestern catalog...")
        print("-" * 50)
        
        departments_data = scrape_departments.scrape_departments()
        
        if not departments_data:
            print("❌ No departments found. Aborting.")
            return
        
        print(f"✅ Successfully scraped {len(departments_data)} departments")
        
        # Save to JSON (for backup/debugging)
        output_file = scrape_departments.save_departments_json(departments_data)
        print(f"💾 Saved backup to: {output_file}")
        
        # Step 2: Upload to database
        print(f"\nSTEP 2: Uploading departments to database...")
        print("-" * 40)
        
        # Show sample data
        print("Sample departments to upload:")
        for i, dept in enumerate(departments_data[:5], 1):
            print(f"  {i}. {dept['name']} ({dept['code']})")
        
        if len(departments_data) > 5:
            print(f"  ... and {len(departments_data) - 5} more")
        
        # Confirm upload
        confirm = input(f"\nProceed with uploading {len(departments_data)} departments? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Upload cancelled by user.")
            print(f"📄 Department data is still available in: {output_file}")
            return
        
        # Upload departments
        results = upload_departments(departments_data)
        
        # Print final summary
        print("\n" + "=" * 55)
        print("🎯 FINAL RESULTS")
        print("=" * 55)
        print(f"Departments scraped: {len(departments_data)}")
        print(f"Departments uploaded: {results['uploaded']}")
        print(f"Upload errors: {len(results['errors'])}")
        
        if results['errors']:
            print("\n❌ Upload errors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        success_rate = (results['uploaded'] / results['total']) * 100 if results['total'] > 0 else 0
        
        if success_rate == 100:
            print(f"\n🎉 SUCCESS! All departments uploaded successfully!")
        elif success_rate >= 90:
            print(f"\n✅ Mostly successful: {success_rate:.1f}% upload rate")
        else:
            print(f"\n⚠️  Partial success: {success_rate:.1f}% upload rate")
        
        print(f"📄 Backup data available in: {output_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()