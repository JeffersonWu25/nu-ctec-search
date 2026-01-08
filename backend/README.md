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

#### Scrape and Upload Departments
```bash
# Scrape departments from Northwestern and upload to database
python -m app.jobs.scrape_departments

# Preview what would be scraped/uploaded
python -m app.jobs.scrape_departments --dry-run

# Save scraped data but don't upload
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

#### Scrape and Upload Course Catalog
```bash
# Scrape all departments and upload
python -m app.jobs.scrape_catalog

# Scrape specific departments only
python -m app.jobs.scrape_catalog --departments COMP_SCI,MATH,ECON

# Limit to first 5 departments (testing)
python -m app.jobs.scrape_catalog --limit 5

# Preview upload changes
python -m app.jobs.scrape_catalog --dry-run
```

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

```bash
# Update all courses with department_id based on course codes
python -m app.jobs.update_course_departments

# Preview changes
python -m app.jobs.update_course_departments --dry-run

# Test on small sample
python -m app.jobs.update_course_departments --sample 10 --dry-run
```

### 📋 CTEC Processing

#### Upload Single CTEC
```bash
# Upload a single CTEC PDF
python -m app.jobs.upload_ctecs --file path/to/ctec.pdf

# Preview what would be uploaded
python -m app.jobs.upload_ctecs --file path/to/ctec.pdf --dry-run

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
```

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

4. **Load course catalog** (if you have courses):
   ```bash
   python -m app.jobs.scrape_catalog --limit 3  # Start small
   ```

5. **Link courses to departments**:
   ```bash
   python -m app.jobs.update_course_departments
   ```

### Regular Data Updates

1. **Update departments** (occasionally):
   ```bash
   python -m app.jobs.scrape_departments
   ```

2. **Update course catalog** (semester/yearly):
   ```bash
   python -m app.jobs.scrape_catalog
   python -m app.jobs.update_course_departments  # Link new courses
   ```

3. **Process new CTECs** (regularly):
   ```bash
   python -m app.jobs.upload_ctecs --all --upload-dir /path/to/new/ctecs
   ```

### Development/Testing

1. **Always use dry-run first**:
   ```bash
   python -m app.jobs.upload_catalog --dry-run
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
```

#### CTEC Jobs
```bash
# Batch upload with error tolerance
python -m app.jobs.upload_ctecs --all --continue-on-errors --upload-dir /ctecs
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

Start with department setup and work your way up to full CTEC processing!