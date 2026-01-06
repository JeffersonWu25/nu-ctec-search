# CTEC Upload System

A complete pipeline for parsing CTEC PDF files and uploading them to the Northwestern course database.

## Features

- ✅ **Interactive Terminal Interface** - User-friendly menu system
- ✅ **Parse & Upload Pipeline** - Automatically parses PDFs and uploads to database  
- ✅ **Fuzzy Instructor Matching** - Handles name variations intelligently
- ✅ **Duplicate Handling** - Updates existing course offerings gracefully
- ✅ **Error Recovery** - Continues processing on individual file failures
- ✅ **Progress Tracking** - Real-time status updates and final statistics

## Quick Start

### 1. Setup Database (one-time)
```bash
# Add the unique constraint to prevent duplicates
# Run this SQL in your Supabase SQL editor:
cat ../add_course_offering_constraint.sql

# Initialize survey questions and options
cd ..
python setup_survey_questions.py
```

### 2. Add PDF Files
Place your CTEC PDF files in: `docs/upload/`

### 3. Run Upload System

**Interactive Mode (Recommended):**
```bash
cd backend/upload
python upload_ctecs.py
```

**Command Line Mode:**
```bash
# Upload single file
python upload_ctecs.py --file path/to/ctec.pdf

# Upload all files in docs/upload
python upload_ctecs.py --all

# Upload from custom directory
python upload_ctecs.py --all --upload-dir /path/to/pdfs
```

## How It Works

1. **Parse**: Each PDF is processed using the CTEC parser via subprocess
2. **Validate**: Parsed data is validated for completeness
3. **Upload**: Data is inserted/updated in the database:
   - Course information (creates if new)
   - Instructor information (with fuzzy matching)
   - Course offering (updates if duplicate exists)
   - Student comments
   - Survey response distributions

## File Structure

```
backend/upload/
├── upload_ctecs.py          # Main entry point
├── terminal_interface.py    # Interactive menu system
├── upload_pipeline.py       # Core processing logic
├── pdf_processor.py         # PDF parsing integration
├── instructor_matcher.py    # Fuzzy instructor name matching
└── utils.py                # Database utilities
```

## Error Handling

- **Parse Failures**: Logged and skipped, processing continues
- **Upload Failures**: Logged with details, processing continues  
- **Duplicate Offerings**: Existing data is updated with new information
- **Database Errors**: Detailed error messages with recovery suggestions

## Dependencies

- Existing CTEC parser (`backend/parser/`)
- Supabase client (`backend/api/supabase_client.py`)
- Survey questions setup (`backend/setup_survey_questions.py`)

## Troubleshooting

**"Parser script not found"**: Make sure the batch parser exists at `backend/parser/batch_parse_ctecs.py`

**"Upload directory not found"**: The `docs/upload/` directory will be created automatically

**"Survey questions not found"**: Run `python setup_survey_questions.py` first

**Database constraint errors**: Apply the SQL constraint from `add_course_offering_constraint.sql`