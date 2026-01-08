"""
Northwestern CTEC Parser - Class-based implementation.

This module provides a comprehensive parser for Northwestern University's 
Course and Teacher Evaluation (CTEC) PDF documents.
"""

import re
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pypdf import PdfReader
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from .constants import DEPARTMENTS, CLASS_YEAR, DISTRIBUTION_REQUIREMENT, PRIOR_INTEREST, TIME_RANGES


@dataclass
class ParserConfig:
    """Configuration options for CTECParser."""
    debug: bool = False
    ocr_dpi: int = 300
    ocr_timeout_seconds: int = 30
    validate_ocr_totals: bool = True
    continue_on_ocr_errors: bool = False
    extract_comments: bool = True
    extract_demographics: bool = True
    extract_time_survey: bool = True


@dataclass
class CourseInfo:
    """Course metadata extracted from CTEC."""
    code: str
    title: str
    section: str
    instructor: str
    quarter: str
    year: int
    audience_size: Optional[int] = None
    response_count: Optional[int] = None
    

@dataclass
class CTECData:
    """Complete CTEC data structure."""
    course_info: CourseInfo
    comments: List[str]
    survey_responses: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self.course_info),
            'comments': self.comments,
            'survey_responses': self.survey_responses
        }


class CTECParsingError(Exception):
    """Custom exception for CTEC parsing errors."""
    pass


class CTECParser:
    """
    Northwestern CTEC PDF Parser.
    
    Extracts course information, ratings, demographics, comments, and time survey data
    from Northwestern University Course and Teacher Evaluation (CTEC) PDF documents.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None, debug: bool = False):
        """
        Initialize the CTEC parser.
        
        Args:
            config: Parser configuration options
            debug: Enable debug output (deprecated, use config.debug instead)
        """
        if config is None:
            config = ParserConfig(debug=debug)
        elif debug:  # Override config debug if explicitly set
            config.debug = debug
            
        self.config = config
        self.debug = config.debug  # Maintain backward compatibility
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Initialize regex patterns for text extraction."""
        # Course info patterns
        self.course_pattern1 = re.compile(
            r"Student Report for (.*?)\((.*?)\)\s*\(([^)]+)\)"
        )
        self.course_pattern2 = re.compile(
            r"Student Report for ([^:]+):\s*(.*?)\s*\(([^)]+)\)"
        )
        
        # Term info pattern
        self.term_pattern = re.compile(
            r"Course and Teacher Evaluations CTEC (Spring|Fall|Winter|Summer) (\d{4})"
        )
        
        # Audience and response patterns - handle both formats
        self.audience_pattern = re.compile(
            r"Courses?\s+Audience\s*:?\s*(\d+)", re.IGNORECASE
        )
        self.response_pattern = re.compile(
            r"Responses?\s+Received\s*:?\s*(\d+)", re.IGNORECASE
        )
        
        # OCR distribution patterns - flexible to handle various formats
        # Matches: "1-Very Low (0)", "2 (1)", "6-Very High (24)", etc.
        self.dist_pattern = re.compile(
            r"(?i)([1-6])(?:[-–—]\s*(?:Very\s+Low|Very\s+High|[A-Za-z\s–—-]*?))?\s*\((\d+)\)"
        )
        self.total_pattern = re.compile(
            r"(?i)(?:total|\[?\s*total\s*\]?)\s*\((\d+)\)", 
            re.IGNORECASE
        )
        
        # Survey question patterns - keys match actual question text
        self.survey_questions = {
            "Provide an overall rating of the instruction": r"1\.\s*Provide an overall rating of the instruction.*?(?=2\.\s*Provide)",
            "Provide an overall rating of the course": r"2\.\s*Provide an overall rating of the course.*?(?=3\.\s*Estimate)",
            "Estimate how much you learned in the course": r"3\.\s*Estimate how much you learned in the course.*?(?=4\.\s*Rate)",
            "Rate the effectiveness of the course in challenging you intellectually": r"4\.\s*Rate the effectiveness of the course in challenging you intellectually.*?(?=5\.\s*Rate)",
            "Rate the effectiveness of the instructor in stimulating your interest in the subject": r"5\.\s*Rate the effectiveness of the instructor in stimulating your interest in the subject.*"
        }
    
    def _log_debug(self, message: str):
        """Log debug message if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract raw text from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Raw text extracted from all pages
            
        Raises:
            CTECParsingError: If file doesn't exist or text extraction fails
        """
        if not os.path.exists(pdf_path):
            raise CTECParsingError(f"PDF file not found: {pdf_path}")
        
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            if not text.strip():
                raise CTECParsingError(f"No text extracted from {pdf_path}")
            
            return text
        except Exception as e:
            raise CTECParsingError(f"Failed to extract text from {pdf_path}: {e}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text with normalized whitespace
        """
        if not text:
            return ""
        return ' '.join(line.strip() for line in text.splitlines() if line.strip())
    
    def _extract_course_info(self, text: str) -> CourseInfo:
        """
        Extract course information from cleaned text.
        
        Args:
            text: Cleaned text from PDF
            
        Returns:
            CourseInfo object with course metadata
            
        Raises:
            CTECParsingError: If course info cannot be extracted
        """
        if not text:
            raise CTECParsingError("Empty text provided for course info extraction")
        
        # Try both patterns
        match1 = self.course_pattern1.search(text)
        match2 = self.course_pattern2.search(text)
        
        # Select the match that appears earlier
        selected_match = None
        pattern_used = None
        
        if match1 and match2:
            selected_match = match1 if match1.start() <= match2.start() else match2
            pattern_used = 1 if selected_match == match1 else 2
        elif match1:
            selected_match = match1
            pattern_used = 1
        elif match2:
            selected_match = match2
            pattern_used = 2
        
        if not selected_match:
            raise CTECParsingError("Could not match course info pattern in text")
        
        try:
            if pattern_used == 1:
                title = selected_match.group(1).strip()
                codes_part = selected_match.group(2).strip()
                instructor = selected_match.group(3).strip()
                
                # Extract code and section
                codes = [item.split(':')[0].strip() for item in codes_part.split(',') if ':' in item]
                full_code = codes[0]
                
                # Split by last underscore to separate course code from section
                if '_' in full_code:
                    code_and_section = full_code.rsplit('_', 1)
                    course_code = code_and_section[0]
                    section = code_and_section[1] if len(code_and_section) > 1 else ""
                else:
                    course_code = full_code
                    section = ""
                
                return CourseInfo(
                    title=title,
                    code=course_code,
                    section=section,
                    instructor=instructor,
                    quarter="",  # Will be filled by _extract_term_info
                    year=0       # Will be filled by _extract_term_info
                )
            else:  # pattern_used == 2
                code = selected_match.group(1).strip()
                title = selected_match.group(2).strip()
                instructor = selected_match.group(3).strip()
                
                # Split by last underscore to separate course code from section
                if '_' in code:
                    code_parts = code.rsplit('_', 1)
                    course_code = code_parts[0]
                    section = code_parts[1] if len(code_parts) > 1 else ""
                else:
                    course_code = code
                    section = ""
                
                return CourseInfo(
                    title=title,
                    code=course_code,
                    section=section,
                    instructor=instructor,
                    quarter="",  # Will be filled by _extract_term_info
                    year=0       # Will be filled by _extract_term_info
                )
        except (IndexError, ValueError) as e:
            raise CTECParsingError(f"Error processing course info match: {e}")
    
    def _extract_term_info(self, text: str) -> tuple[str, int]:
        """
        Extract quarter and year from text.
        
        Args:
            text: Cleaned text from PDF
            
        Returns:
            Tuple of (quarter, year)
            
        Raises:
            CTECParsingError: If term info cannot be extracted
        """
        match = self.term_pattern.search(text)
        if not match:
            raise CTECParsingError("Could not extract term information")
        
        return match.group(1), int(match.group(2))
    
    def _extract_audience_and_response_metadata(self, raw_text: str) -> tuple[Optional[int], Optional[int]]:
        """
        Extract audience size and response count from raw text.
        
        Args:
            raw_text: Raw text from PDF (before cleaning)
            
        Returns:
            Tuple of (audience_size, response_count)
        """
        audience_size = None
        response_count = None
        
        # Look for the specific patterns in CTEC format:
        # The PDF format has header lines followed by numbers:
        # "Courses Audience :"       (line 1)
        # "Responses Received :"     (line 2)  
        # "Response Ratio :"         (line 3)
        # ...
        # "217"                      (line 7 - audience)
        # "183"                      (line 8 - responses)
        # "84.3%"                    (line 9 - ratio)
        
        lines = raw_text.split('\n')
        
        # Find the positions of the headers
        audience_line = None
        response_line = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if re.match(r'^Courses?\s+Audience\s*:\s*$', line_stripped, re.IGNORECASE):
                audience_line = i
            elif re.match(r'^Responses?\s+Received\s*:\s*$', line_stripped, re.IGNORECASE):
                response_line = i
        
        # If we found the headers, extract the corresponding numbers
        if audience_line is not None and response_line is not None:
            # Look for numeric lines after the headers
            numbers = []
            start_search = max(audience_line, response_line) + 1
            
            for i in range(start_search, min(start_search + 10, len(lines))):
                number_match = re.match(r'^\s*(\d+)\s*$', lines[i])
                if number_match:
                    numbers.append(int(number_match.group(1)))
                    if len(numbers) >= 2:  # We have both audience and responses
                        break
            
            # Assign numbers based on header order
            if len(numbers) >= 2:
                if audience_line < response_line:
                    audience_size = numbers[0]
                    response_count = numbers[1]
                else:
                    response_count = numbers[0] 
                    audience_size = numbers[1]
        
        self._log_debug(f"Extracted audience: {audience_size}, responses: {response_count}")
        
        return audience_size, response_count
    
    def _extract_comments(self, raw_text: str) -> List[str]:
        """
        Extract student comments from raw text.
        
        Args:
            raw_text: Raw text from PDF (not cleaned)
            
        Returns:
            List of student comments
        """
        # Find the comments section
        start_phrase = "Please summarize your reaction to this course focusing on the aspects that were most important to you."
        start = raw_text.find(start_phrase)
        if start == -1:
            return []
        
        start += len(start_phrase)
        end = raw_text.find("DEMOGRAPHICS", start)
        if end == -1:
            end = len(raw_text)
        
        # Extract and clean comments section
        comment_text = raw_text[start:end].strip()
        comment_text = comment_text.replace("Comments", "")
        comment_text = re.sub(r"Student Report for .*?\d+/\d+", "", comment_text, flags=re.DOTALL)
        
        lines = [line.strip() for line in comment_text.split('\n') if line.strip()]
        
        # Group lines into comments (comments typically start with uppercase)
        comments = []
        current = []
        
        for line in lines:
            if line and line[0].isupper() and current:
                comments.append(' '.join(current))
                current = [line]
            else:
                current.append(line)
        
        if current:
            comments.append(' '.join(current))
        
        self._log_debug(f"Extracted {len(comments)} comments")
        return comments
    
    def _extract_demographic_distributions(self, text: str) -> Dict[str, Dict]:
        """
        Extract demographic distributions from text.
        
        Args:
            text: Cleaned text from PDF
            
        Returns:
            Dictionary with demographic distributions
        """
        # Find demographics section
        start = text.find("DEMOGRAPHICS")
        if start == -1:
            return {}
        
        demographics_text = text[start:]
        distributions = {
            "What is the name of your school?": {},
            "Your Class": {},
            "What is your reason for taking the course? (mark all that apply)": {},
            "What was your Interest in this subject before taking the course?": {}
        }
        
        # Extract distributions for each category
        categories = [
            (DEPARTMENTS, "What is the name of your school?"),
            (CLASS_YEAR, "Your Class"),
            (DISTRIBUTION_REQUIREMENT, "What is your reason for taking the course? (mark all that apply)"),
            (PRIOR_INTEREST, "What was your Interest in this subject before taking the course?")
        ]
        
        for items, category in categories:
            for item in items:
                pattern = rf"{re.escape(item)}\s+(\d+)\s+[\d.]+%"
                match = re.search(pattern, demographics_text, flags=re.MULTILINE)
                if match:
                    key = item
                    if category == "What was your Interest in this subject before taking the course?":
                        if item == "1-Not interested at all":
                            key = "1"
                        elif item == "6-Extremely interested":
                            key = "6"
                        key = int(key) if key.isdigit() else key
                    
                    distributions[category][key] = int(match.group(1))
        
        return distributions
    
    def _extract_time_survey(self, text: str) -> Dict[str, Dict]:
        """
        Extract time survey distributions from text.
        
        Args:
            text: Cleaned text from PDF
            
        Returns:
            Dictionary with time survey distributions
        """
        start = text.find("TIME-SURVEY QUESTION")
        if start == -1:
            return {}
        
        end = text.find("ESSAY QUESTIONS")
        if end == -1:
            end = text.find("Essay Questions")
            if end == -1:
                end = len(text)
        
        time_survey_text = text[start:end]
        
        # Extract the actual question text
        question_match = re.search(
            r"Estimate the average number of hours per week you spent on this course outside of class and lab time\.?", 
            time_survey_text, 
            flags=re.IGNORECASE
        )
        
        question_key = "Estimate the average number of hours per week you spent on this course outside of class and lab time"
        if not question_match:
            # Fallback to shorter version if full text not found
            question_key = "Estimate the average number of hours per week you spent on this course outside of class and lab time"
        
        distributions = {question_key: {}}
        
        for time_range in TIME_RANGES:
            pattern = rf"{re.escape(time_range)}\s+(\d+)\s+[\d.]+%"
            match = re.search(pattern, time_survey_text, flags=re.MULTILINE)
            if match:
                distributions[question_key][time_range] = int(match.group(1))
        
        return distributions
    
    def _extract_rating_distribution_from_question(self, text: str, file_identifier: str = "") -> Dict[int, int]:
        """
        Extract rating distribution from a single question's OCR text.
        
        Args:
            text: OCR text for one question
            file_identifier: File path for error reporting
            
        Returns:
            Distribution dictionary {rating: count}
            
        Raises:
            CTECParsingError: If OCR validation fails
        """
        pairs = self.dist_pattern.findall(text)
        distribution = {int(k): int(v) for k, v in pairs}
        
        # Validate against OCR total if enabled
        if self.config.validate_ocr_totals:
            total_match = self.total_pattern.search(text)
            if total_match:
                ocr_total = int(total_match.group(1))
                calculated_total = sum(distribution.values())
                
                if ocr_total != calculated_total:
                    # Try alternative extraction patterns before failing
                    alt_distribution = self._try_alternative_distribution_extraction(text)
                    if alt_distribution:
                        alt_total = sum(alt_distribution.values())
                        if alt_total == ocr_total:
                            self._log_debug(f"Alternative extraction successful: {alt_distribution}")
                            return alt_distribution
                    
                    error_msg = f"OCR validation failed for {file_identifier}: Total mismatch (OCR: {ocr_total}, Calculated: {calculated_total})"
                    self._log_debug(error_msg)
                    self._log_debug(f"Raw distribution found: {distribution}")
                    self._log_debug(f"OCR text snippet: {text[:200]}...")
                    raise CTECParsingError(error_msg)
        
        return distribution
    
    def _try_alternative_distribution_extraction(self, text: str) -> Optional[Dict[int, int]]:
        """
        Try alternative patterns for extracting rating distributions when the primary pattern fails.
        
        Args:
            text: OCR text for one question
            
        Returns:
            Alternative distribution dictionary or None if no valid pattern found
        """
        # Alternative pattern 1: Numbers with different bracket styles
        alt_pattern1 = re.compile(r"([1-6])[^\d]*?[\(\[\{](\d+)[\)\]\}]")
        pairs1 = alt_pattern1.findall(text)
        if pairs1:
            distribution1 = {int(k): int(v) for k, v in pairs1 if k.isdigit() and v.isdigit()}
            if len(distribution1) >= 3:  # At least 3 ratings found
                self._log_debug(f"Alternative pattern 1 found: {distribution1}")
                return distribution1
        
        # Alternative pattern 2: Look for standalone numbers that might be counts
        # Find lines with rating-like structure
        lines = text.split('\n')
        distribution2 = {}
        for line in lines:
            # Look for patterns like "1 (5)" or "Very Low 3" etc.
            match = re.search(r"(?:^|\s)([1-6])(?:\s*[-–—]\s*\w+)?\s*[\(\[]?(\d+)[\)\]]?", line.strip())
            if match:
                rating, count = int(match.group(1)), int(match.group(2))
                if 1 <= rating <= 6 and count < 1000:  # Sanity check
                    distribution2[rating] = count
        
        if len(distribution2) >= 3:
            self._log_debug(f"Alternative pattern 2 found: {distribution2}")
            return distribution2
        
        return None
    
    def _extract_survey_distributions_from_ocr(self, ocr_text: str, file_identifier: str = "") -> Dict[str, Dict]:
        """
        Extract distributions for survey questions 1-5 from OCR text.
        
        Args:
            ocr_text: Raw OCR text from pages 2-3
            file_identifier: File path for error reporting
            
        Returns:
            Dictionary with survey question distributions
            
        Raises:
            CTECParsingError: If extraction or validation fails
        """
        results = {}
        validation_errors = []
        
        for question, pattern in self.survey_questions.items():
            match = re.search(pattern, ocr_text, flags=re.S)
            if match:
                block = match.group(0)
                try:
                    results[question] = self._extract_rating_distribution_from_question(block, file_identifier)
                except CTECParsingError as e:
                    validation_errors.append(f"{question}: {str(e)}")
        
        if validation_errors:
            error_summary = f"OCR validation failed for {len(validation_errors)} questions: " + "; ".join(validation_errors)
            raise CTECParsingError(error_summary)
        
        return results
    
    def _extract_ocr_from_page(self, page_img: Image.Image) -> str:
        """
        Extract OCR text from a page image.
        
        Args:
            page_img: PIL Image of the page
            
        Returns:
            OCR text from the page
        """
        # Use red channel for better OCR accuracy
        red_channel = page_img.split()[0] if len(page_img.split()) >= 3 else page_img.convert("L")
        return pytesseract.image_to_string(red_channel, config=r'--oem 3 --psm 3')
    
    def _extract_survey_ratings_via_ocr(self, pdf_path: str) -> Dict[str, Dict]:
        """
        Extract survey ratings (questions 1-5) using OCR on pages 2-3.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with rating distributions
            
        Raises:
            CTECParsingError: If OCR processing fails
        """
        try:
            # Convert pages 2-3 to images (0-indexed: pages 1 and 2)
            pages = convert_from_path(pdf_path, dpi=self.config.ocr_dpi)
            if len(pages) < 3:
                raise CTECParsingError(f"PDF has fewer than 3 pages: {len(pages)}")
            
            pages = pages[1:3]  # Pages 2-3
            full_ocr_text = ""
            
            for i, page_img in enumerate(pages):
                try:
                    full_ocr_text += self._extract_ocr_from_page(page_img)
                except Exception as e:
                    raise CTECParsingError(f"OCR failed on page {i + 2}: {e}")
            
            self._log_debug(f"OCR text extracted: {len(full_ocr_text)} characters")
            
            return self._extract_survey_distributions_from_ocr(full_ocr_text, pdf_path)
            
        except Exception as e:
            if isinstance(e, CTECParsingError):
                raise
            raise CTECParsingError(f"Failed to extract survey ratings from {pdf_path}: {e}")
    
    def parse_ctec(self, pdf_path: str) -> CTECData:
        """
        Parse a complete CTEC PDF file.
        
        Args:
            pdf_path: Path to the CTEC PDF file
            
        Returns:
            CTECData object with all extracted information
            
        Raises:
            CTECParsingError: If parsing fails at any stage
        """
        self._log_debug(f"Starting to parse {pdf_path}")
        
        try:
            # Extract text
            raw_text = self._extract_text_from_pdf(pdf_path)
            cleaned_text = self._clean_text(raw_text)
            
            # Extract course information
            course_info = self._extract_course_info(cleaned_text)
            quarter, year = self._extract_term_info(cleaned_text)
            audience_size, response_count = self._extract_audience_and_response_metadata(raw_text)
            course_info.quarter = quarter
            course_info.year = year
            course_info.audience_size = audience_size
            course_info.response_count = response_count
            
            # Extract comments (if enabled)
            comments = []
            if self.config.extract_comments:
                comments = self._extract_comments(raw_text)
            
            # Extract survey responses
            survey_responses = {}
            
            # Questions 1-5 (OCR-based)
            try:
                rating_distributions = self._extract_survey_ratings_via_ocr(pdf_path)
                survey_responses.update(rating_distributions)
            except CTECParsingError as e:
                self._log_debug(f"Failed to extract rating distributions: {e}")
                if not self.config.continue_on_ocr_errors:
                    raise
            
            # Demographics (questions 6-10)
            if self.config.extract_demographics:
                demographic_distributions = self._extract_demographic_distributions(cleaned_text)
                survey_responses.update(demographic_distributions)
            
            # Time survey (question 11)
            if self.config.extract_time_survey:
                time_distributions = self._extract_time_survey(cleaned_text)
                survey_responses.update(time_distributions)
            
            self._log_debug(f"Successfully parsed {pdf_path}")
            
            return CTECData(
                course_info=course_info,
                comments=comments,
                survey_responses=survey_responses
            )
            
        except Exception as e:
            if isinstance(e, CTECParsingError):
                raise
            raise CTECParsingError(f"Failed to parse {pdf_path}: {e}")
    
    def parse_multiple_ctecs(self, pdf_paths: List[str], continue_on_error: bool = True) -> Dict[str, Any]:
        """
        Parse multiple CTEC PDF files.
        
        Args:
            pdf_paths: List of paths to CTEC PDF files
            continue_on_error: Continue processing other files if one fails
            
        Returns:
            Dictionary with results and errors:
            {
                'successful': {file_path: CTECData, ...},
                'failed': {file_path: error_message, ...}
            }
        """
        results = {'successful': {}, 'failed': {}}
        
        for pdf_path in pdf_paths:
            try:
                ctec_data = self.parse_ctec(pdf_path)
                results['successful'][pdf_path] = ctec_data
                self._log_debug(f"✓ Successfully parsed {pdf_path}")
            except Exception as e:
                error_msg = str(e)
                results['failed'][pdf_path] = error_msg
                self._log_debug(f"✗ Failed to parse {pdf_path}: {error_msg}")
                
                if not continue_on_error:
                    raise
        
        return results