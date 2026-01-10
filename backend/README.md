# Northwestern CTEC Search Backend

A production-ready backend system for processing Northwestern University's Course and Teacher Evaluation (CTEC) data, course catalogs, and department information.

## 🏗️ Architecture

```
backend/app/
├── routes/        # API endpoints (FastAPI - future)
├── services/      # Business logic orchestration  
├── db/           # Database operations only
├── parsing/      # Document processing (CTECs)
├── ingestion/    # External data acquisition (scraping)
├── jobs/         # CLI entry points
└── utils/        # Shared utilities
```

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**:
   ```bash
   cd backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   Create a `.env` file in the backend directory:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_SECRET_KEY=your_supabase_secret_key
   ```

3. **Database Setup**:
   Ensure your Supabase database has the required tables (departments, courses, etc.)

## 📋 Available Jobs

All jobs are run as Python modules with comprehensive help:

```bash
python -m app.jobs.<job_name> --help
```

### 🏫 Department Management

This goes to this webpage: https://catalogs.northwestern.edu/undergraduate/courses-az/. It identifies all of the departments listed on the page and
updates the departments table in Supabase. This will likely only ever need to run once because the departments do not change.

#### Scrape and Upload Departments
```bash
# Scrape departments from Northwestern and upload to database
python -m app.jobs.scrape_departments

# Preview what would be scraped/uploaded
python -m app.jobs.scrape_departments --dry-run

# Save scraped data in scraped_data folder but don't upload
python -m app.jobs.scrape_departments --save-only
```

#### Upload Departments from File
```bash
# Upload from default file (scraped_data/departments_mapping.json)
python -m app.jobs.upload_departments

# Upload from custom file
python -m app.jobs.upload_departments /path/to/departments.json

# Preview changes without uploading
python -m app.jobs.upload_departments --dry-run

# Scrape fresh data and upload in one command
python -m app.jobs.upload_departments --scrape
```

### 📚 Course Catalog Management

This goes to this webpage: https://catalogs.northwestern.edu/undergraduate/courses-az/. It creates a list of the links to the department page for each department listed on that website. It then goes through each department page that looks like: https://catalogs.northwestern.edu/undergraduate/courses-az/afst/ and it parses out the description, requirements, and course prerequisites. It then updates the courses table for existing rows. it DOES NOT create new courses if they do not exit. It matches the rows in the requirements table with the correct courses.

#### Scrape and Upload Course Catalog
```bash
# Scrape all departments and upload (with detailed validation summary)
python -m app.jobs.scrape_catalog

# Scrape specific departments only
python -m app.jobs.scrape_catalog --departments COMP_SCI,MATH,ECON

# Limit to first 5 departments (testing)
python -m app.jobs.scrape_catalog --limit 5

# Preview upload changes
python -m app.jobs.scrape_catalog --dry-run

# Only update courses with completely empty catalog data (gap-filling mode)
python -m app.jobs.scrape_catalog --empty-only


#### Upload Catalog from File
```bash
# Upload from default file (scraped_data/catalog_data.json)
python -m app.jobs.upload_catalog

# Upload from custom file
python -m app.jobs.upload_catalog /path/to/catalog.json

# Preview changes
python -m app.jobs.upload_catalog --dry-run
```

### 🔗 Course-Department Mapping

This links newly uploaded courses with their department in the department table

```bash
# Update all courses with department_id based on course codes
python -m app.jobs.update_course_departments

# Preview changes
python -m app.jobs.update_course_departments --dry-run

# Test on small sample
python -m app.jobs.update_course_departments --sample 10 --dry-run
```

### 📋 CTEC Processing

This uploads a new CTEC to the database which upserts into the courses and course offerings table, along with adding its comment and ratings

#### Upload Single CTEC
```bash
# Upload a single CTEC PDF
python -m app.jobs.upload_ctecs --file path/to/ctec.pdf

# Preview what would be uploaded
python -m app.jobs.upload_ctecs --file path/to/ctec.pdf --dry-run

# Show detailed parsed data in JSON format
python -m app.jobs.upload_ctecs --file path/to/ctec.pdf --dry-run --verbose

# Enable debug mode for parsing issues
python -m app.jobs.upload_ctecs --file path/to/ctec.pdf --debug
```

#### Batch Upload CTECs
```bash
# Upload all PDFs in docs/upload directory
python -m app.jobs.upload_ctecs --all

# Use custom directory
python -m app.jobs.upload_ctecs --all --upload-dir /path/to/pdfs

# Continue processing even if some PDFs fail OCR validation
python -m app.jobs.upload_ctecs --all --continue-on-errors

# Show detailed data for each file (useful for debugging)
python -m app.jobs.upload_ctecs --all --dry-run --verbose
```

#### CTEC Upload Options

- `--file path.pdf`: Upload a single PDF file
- `--all`: Process all PDFs in the upload directory  
- `--upload-dir path`: Use custom directory instead of docs/upload
- `--dry-run`: Preview changes without uploading to database
- `--verbose`: Show detailed parsed data in JSON format (includes all comments, ratings, demographics)
- `--debug`: Enable debug output for troubleshooting parsing issues
- `--continue-on-errors`: Continue processing other files if OCR validation fails

### 🤖 AI Summary Management

These commands intelligently manage AI-generated summaries with automatic staleness detection and dependency propagation.

#### Refresh AI Summaries
```bash
# Refresh all stale AI summaries (recommended)
python -m app.jobs.refresh_ai_summaries

# Preview what summaries need updates
python -m app.jobs.refresh_ai_summaries --dry-run

# Refresh only course offering summaries
python -m app.jobs.refresh_ai_summaries --entity-type course_offering

# Refresh only instructor summaries  
python -m app.jobs.refresh_ai_summaries --entity-type instructor

# Refresh only course summaries
python -m app.jobs.refresh_ai_summaries --entity-type course

# Force refresh all summaries (ignores staleness)
python -m app.jobs.refresh_ai_summaries --force
```

#### How AI Summary Refresh Works

The system uses intelligent staleness detection:
- **Course Offering Summaries**: Refreshed when new comments are added to that offering
- **Instructor Summaries**: Refreshed when any comments change for courses they teach
- **Course Summaries**: Refreshed when course offering summaries change

**Dependency Order**: The job automatically refreshes in the correct order:
1. Course offerings first (based on raw comments)
2. Instructors second (based on comments across all their offerings) 
3. Courses last (based on their offering summaries)

**Efficiency**: Only entities with actual changes are updated, making the job fast and cost-effective.

### 🔧 System Setup

```bash
# Initialize survey questions and options in database
python -m app.jobs.setup_survey_questions

# Preview what would be created
python -m app.jobs.setup_survey_questions --dry-run
```

## 🔄 Common Workflows

### Initial System Setup

1. **Setup database tables** (if not already done)
2. **Initialize survey questions**:
   ```bash
   python -m app.jobs.setup_survey_questions
   ```

3. **Load departments**:
   ```bash
   python -m app.jobs.scrape_departments
   ```
   ```

### Regular Data Updates

2. **Update Requirements, Descriptions, Prerequisites and Maybe Departments** (rarely):
   ```bash
   # Full catalog update with comprehensive validation
   python -m app.jobs.scrape_catalog
   python -m app.jobs.update_course_departments  # links courses to department
   
   # OR gap-filling mode to only update empty courses (safer)
   python -m app.jobs.scrape_catalog --empty-only
   ```

3. **Process new CTECs** (Every quarter when new CTECs Drop):
   ```bash
   python -m app.jobs.upload_ctecs --all --upload-dir /path/to/new/ctecs
   python -m app.jobs.scrape_catalog # adds the descriptions, prerequisites
   python -m app.jobs.update_course_departments  # links courses to department
   python -m app.jobs.refresh_ai_summaries  # update AI summaries for new data
   ```

### Development/Testing

1. **Always use dry-run first**:
   ```bash
   python -m app.jobs.upload_catalog --dry-run
   python -m app.jobs.refresh_ai_summaries --dry-run
   ```

2. **Test with samples**:
   ```bash
   python -m app.jobs.update_course_departments --sample 5 --dry-run
   ```

3. **Use debug mode for issues**:
   ```bash
   python -m app.jobs.upload_ctecs --file problematic.pdf --debug
   ```

## 📁 Data Files

### Input Files
- **Departments**: `scraped_data/departments_mapping.json`
- **Catalog**: `scraped_data/catalog_data.json`  
- **CTECs**: Any directory with PDF files

### Output/Logs
- **Logs**: `scraped_data/*.log` (one per job)
- **Scraped Data**: `scraped_data/` (automatic backups)

## 🛠️ Advanced Usage

### Environment Variables

Set these in your `.env` file or environment:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key
```

### Job-Specific Options

#### Department Jobs
```bash
# Scrape and upload in one command
python -m app.jobs.upload_departments --scrape --dry-run
```

#### Catalog Jobs  
```bash
# Scrape specific departments and upload
python -m app.jobs.upload_catalog --scrape --departments COMP_SCI,MATH

# Gap-filling mode - only update courses with no catalog data
python -m app.jobs.scrape_catalog --empty-only --dry-run

# Full validation with limited departments for testing
python -m app.jobs.scrape_catalog --limit 10 --dry-run
```

#### CTEC Jobs
```bash
# Batch upload with error tolerance
python -m app.jobs.upload_ctecs --all --continue-on-errors --upload-dir /ctecs
```

#### AI Summary Jobs
```bash
# Check what needs updating without making changes
python -m app.jobs.refresh_ai_summaries --dry-run

# Refresh specific entity types only
python -m app.jobs.refresh_ai_summaries --entity-type instructor

# Force refresh all regardless of staleness (expensive!)
python -m app.jobs.refresh_ai_summaries --force
```

### Custom File Paths
```bash
# Use custom data files
python -m app.jobs.upload_departments /custom/path/departments.json
python -m app.jobs.upload_catalog /custom/path/catalog.json
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Make sure you're in the backend directory
   cd backend
   python -m app.jobs.upload_departments --help
   ```

2. **Database Connection**:
   ```bash
   # Check your .env file has correct credentials
   cat .env
   ```

3. **No Data Found**:
   ```bash
   # Check if data files exist
   ls -la scraped_data/
   ```

4. **Permission Errors**:
   ```bash
   # Check file permissions
   chmod +x backend/app/jobs/*.py
   ```

5. **Catalog Scraping Issues**:
   ```bash
   # Check validation summary for failed departments
   python -m app.jobs.scrape_catalog --limit 5 --dry-run
   
   # Use gap-filling mode if unsure about overwriting data
   python -m app.jobs.scrape_catalog --empty-only --dry-run
   ```

### Debug Mode

Enable detailed logging for any job:
```bash
python -m app.jobs.upload_ctecs --file example.pdf --debug
```

Check logs in `scraped_data/*.log` for detailed error information.

### Dry Run Everything

Always test first with dry run:
```bash
python -m app.jobs.<any_job> --dry-run
```

## 🔮 Future Extensions

The architecture is designed for easy extension:

- **API Layer**: Add FastAPI routes in `app/routes/`
- **New Data Sources**: Add scrapers in `app/ingestion/`
- **New Document Types**: Add parsers in `app/parsing/`
- **New Jobs**: Add CLI scripts in `app/jobs/`
- **Business Logic**: Add services in `app/services/`

## 📞 Support

For issues:
1. Check logs in `scraped_data/*.log`
2. Run with `--dry-run` first
3. Use `--debug` mode for parsing issues
4. Check your environment variables

## 🎉 You're Ready!

Your backend is production-ready with:
- ✅ Professional CLI interfaces
- ✅ Comprehensive error handling  
- ✅ Safe dry-run capabilities
- ✅ Scalable architecture
- ✅ Detailed logging
- ✅ Intelligent AI summary management with staleness detection

Start with department setup and work your way up to full CTEC processing!