"""
Legacy extraction functions - use CTECParser class instead.

This module contains legacy functions that have been superseded by the CTECParser class.
For new code, use ctec_parser.CTECParser instead.
"""

import re
import os
from pypdf import PdfReader
from .ctec_parser import CTECParser
from .constants import DEPARTMENTS, CLASS_YEAR, DISTRIBUTION_REQUIREMENT, PRIOR_INTEREST, TIME_RANGES

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from all pages of a PDF file.

    Args:
        pdf_path: The full path to the PDF file.

    Returns:
        A single string containing the extracted text from all pages,
        or an empty string if the file doesn't exist or text extraction fails.
    """
    # check if the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return ""

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:  # Append text only if extraction was successful for the page
                text += extracted + "\n" # Add newline between pages for clarity before cleaning
        return text
    except Exception as e:
        print(f"Error reading or extracting text from {pdf_path}: {e}")
        return ""

def clean_text(text: str) -> str:
    """
    Cleans up extracted text by:
    1. Splitting into lines based on original line breaks.
    2. Stripping leading/trailing whitespace from each line.
    3. Filtering out lines that become empty after stripping.
    4. Joining the remaining lines back into a single string,
       separated by single spaces. This effectively "unwraps" text.

    Args:
        text: The raw text string (potentially multi-line).

    Returns:
        A single string with cleaned text, joined by spaces.
    """
    if not text:
        return ""
    # Split, strip, filter empty lines, and join with spaces
    return ' '.join(line.strip() for line in text.splitlines() if line.strip())

def extract_code_title_instructor(text: str):
    """
    Extracts course code, title, and instructor from cleaned
    (single-string, space-separated) PDF text using two regex patterns.

    It searches for the first occurrence of a recognizable pattern within
    the entire text block.

    Args:
        cleaned_pdf_text: The output string from the clean_text function.

    Returns:
        {
            "code": str,
            "title": str,
            "section": str,
            "instructor": str
        }
    """
    # Regex Pattern 1: Matches "TITLE (CODES_STRING) (INSTRUCTOR)" format
    # - No ^/$ anchors to allow matching anywhere within the cleaned text.
    # - (.*?): Non-greedy capture for Title and Codes String.
    # - \s*: Optional whitespace.
    # - ([^)]+): Captures Instructor name inside parentheses.
    pattern1 = re.compile(r"Student Report for (.*?)\((.*?)\)\s*\(([^)]+)\)")

    # Regex Pattern 2: Matches "CODE: TITLE (INSTRUCTOR)" format
    # - No ^/$ anchors.
    # - ([^:]+): Captures Code (anything not a colon).
    # - (.*?): Non-greedy capture for Title.
    # - \s*: Optional whitespace.
    # - ([^)]+): Captures Instructor name inside parentheses.
    pattern2 = re.compile(r"Student Report for ([^:]+):\s*(.*?)\s*\(([^)]+)\)")

    course_info = {}
    if not text:
        print("Warning: Input text for extraction is empty.")
        return None

    # Use re.search to find the first occurrence of either pattern
    match1 = pattern1.search(text)
    match2 = pattern2.search(text)

    selected_match = None
    pattern_used = 0 # 0 = None, 1 = Pattern1, 2 = Pattern2

    # Prioritize the match that appears earlier in the text if both somehow match
    if match1 and match2:
        if match1.start() <= match2.start():
            selected_match = match1
            pattern_used = 1
        else:
            selected_match = match2
            pattern_used = 2
    elif match1:
        selected_match = match1
        pattern_used = 1
    elif match2:
        selected_match = match2
        pattern_used = 2

    # Process the selected match based on which pattern was used
    if selected_match and pattern_used == 1:
        try:
            course_title = selected_match.group(1).strip()
            codes_part = selected_match.group(2).strip()
            instructor = selected_match.group(3).strip()
            # Extract base code: split by comma, take part before colon, remove section number
            codes = [item.split(':')[0].strip() for item in codes_part.split(',') if ':' in item]
            # Remove section numbers (e.g., _1, _2) and take first code
            code_and_section = codes[0].rsplit('_', 1)

            course_info['title'] = course_title
            course_info['code'] = code_and_section[0]
            course_info['section'] = code_and_section[1]
            course_info['instructor'] = instructor
        except IndexError:
            print(f"Error processing groups for Pattern 1 match: {selected_match.groups()}")
            return None

    elif selected_match and pattern_used == 2:
        try:
            course_code = selected_match.group(1).strip()
            course_title = selected_match.group(2).strip()
            instructor = selected_match.group(3).strip()
            # Remove section number if present
            code_and_section = course_code.rsplit('_', 1)

            course_info['title'] = course_title
            course_info['code'] = code_and_section[0]
            course_info['section'] = code_and_section[1]
            course_info['instructor'] = instructor
        except IndexError:
            print(f"Error processing groups for Pattern 2 match: {selected_match.groups()}")
            return None

    else:
        # No known pattern was found in the text
        print("Info: Could not match known 'Student Report for...' patterns within the text.")
        return None # Return None if no pattern matched

    return course_info

def extract_quarter_and_year(text: str):
    """
    Extracts quarter and year from CTEC text.

    Args:
        text: The cleaned text string from the PDF.

    Returns:
        {
            "quarter": str,
            "year": int
        }
    """
    term_info = {}
    if not text:
        return {}

    match = re.search(r"Course and Teacher Evaluations CTEC (Spring|Fall|Winter|Summer) (\d{4})", text)
    if not match:
        return {}

    term_info['quarter'] = match.group(1)
    term_info['year'] = int(match.group(2))

    return term_info

def extract_comments(raw_text: str) -> list:
    """
    Extracts comments from CTEC text.

    Args:
        raw_text: The raw text string from the PDF.

    Returns:
        [
            "comment1",
            "comment2",
            "comment3",
            ...
        ]
    """
    # Find the comments section
    if raw_text.find("Please summarize your reaction to this course focusing on the aspects that were most important to you.") == -1:
        return []
    start = (
        raw_text.find("Please summarize your reaction to this course focusing on the aspects that were most important to you.") 
        + len("Please summarize your reaction to this course focusing on the aspects that were most important to you.")
    )
    end = raw_text.find("DEMOGRAPHICS", start)
    if end == -1:
        end = len(raw_text)

    # Get the comments section and split into lines
    comment_text = raw_text[start:end].strip()
    comment_text = comment_text.replace("Comments", "")
    comment_text = re.sub(r"Student Report for .*?\d+/\d+", "", comment_text, flags=re.DOTALL)

    lines = [line.strip() for line in comment_text.split('\n') if line.strip()]

    # Filter out unwanted sections and combine lines into comments
    comments = []
    current = []

    for line in lines:
        if line[0].isupper() and current:
            comments.append(' '.join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        comments.append(' '.join(current))

    print(comments)

    return comments

def extract_demographics(text: str) -> dict:
    """
    Extracts distributions for demographic questions. Questions 6-10

    Args:
        text: The cleaned text string from the PDF.

    Returns:
        {
            "school_name": {Education & SP: int, Communication: int, Graduate School: int, KGSM: int, McCormick: int, Medill: int, Music: int, Summer: int, SPS: int, WCAS: int}
            "class_year": {Freshman: int, Sophomore: int, Junior: int, Senior: int, Graduate: int, Professional: int, Other: int}
            "reason_for_taking_course": {Distribution requirement: int, Major/Minor requirement: int, Elective requirement: int, Non-Degree requirement: int, No requirement: int, Other requirement: int}
            "prior_interest": {1: int, 2: int, 3: int, 4: int, 5: int, 6: int}
        }
    """
    # isolate the text for demographic section
    start = text.find("DEMOGRAPHICS")
    end = len(text)

    demographics_text = text[start:end].strip()

    demographic_distributions = {
        "school_name": {},
        "class_year": {},
        "reason_for_taking_course": {},
        "prior_interest": {},
    }

    for dept in DEPARTMENTS:
        pattern = rf"{re.escape(dept)}\s+(\d+)\s+[\d.]+%"
        match = re.search(pattern, demographics_text, flags=re.MULTILINE)
        if match:
            demographic_distributions["school_name"][dept] = int(match.group(1))

    for year in CLASS_YEAR:
        pattern = rf"{re.escape(year)}\s+(\d+)\s+[\d.]+%"
        match = re.search(pattern, demographics_text, flags=re.MULTILINE)
        if match:
            demographic_distributions["class_year"][year] = int(match.group(1))

    for requirement in DISTRIBUTION_REQUIREMENT:
        pattern = rf"{re.escape(requirement)}\s+(\d+)\s+[\d.]+%"
        match = re.search(pattern, demographics_text, flags=re.MULTILINE)
        if match:
            demographic_distributions["reason_for_taking_course"][requirement] = int(match.group(1))

    for interest in PRIOR_INTEREST:
        pattern = rf"{re.escape(interest)}\s+(\d+)\s+[\d.]+%"
        match = re.search(pattern, demographics_text, flags=re.MULTILINE)
        if match:
            label = interest
            if interest == "1-Not interested at all":
                label = "1"
            if interest == "6-Extremely interested":
                label = "6"
            label = int(label)

            demographic_distributions["prior_interest"][label] = int(match.group(1))

    return demographic_distributions

def extract_time_survey(text: str) -> dict:
    """
    Extracts time survey from CTEC text.

    Args:
        text: The cleaned text string from the PDF.

    Returns:
        {
            "time_survey": {
                "3 or fewer": int,
                "4 - 7": int,
                "8 - 11": int,
                "12 - 15": int,
                "16 - 19": int,
                "20 or more": int
            }
        }
    """
    start = text.find("TIME-SURVEY QUESTION")
    end = text.find("Essay Questions")
    if end == -1:
        end = len(text)
    time_survey_distributions = {"time_survey":{}}

    time_survey_text = text[start:end].strip()

    for time_range in TIME_RANGES:
        pattern = rf"{re.escape(time_range)}\s+(\d+)\s+[\d.]+%"
        match = re.search(pattern, time_survey_text, flags=re.MULTILINE)
        if match:
            time_survey_distributions["time_survey"][time_range] = int(match.group(1))
    return time_survey_distributions

def extract_all_info(pdf_path: str) -> dict:
    """
    DEPRECATED: Use CTECParser class instead.
    
    Legacy wrapper function that uses the new CTECParser class.
    For new code, use ctec_parser.CTECParser directly.

    Args:
        pdf_path: The full path to the PDF file.

    Returns:
        A dictionary containing course info, ratings, comments, term info, and distributions.
    """
    parser = CTECParser()
    ctec_data = parser.parse_ctec(pdf_path)
    return ctec_data.to_dict()
