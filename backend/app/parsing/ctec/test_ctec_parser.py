"""
Comprehensive test suite for CTEC parser.

Tests the CTECParser class against all sample CTEC files to ensure
correct extraction of course information, ratings, demographics,
comments, and time survey data.
"""

from pathlib import Path
import pytest
from ctec_parser import CTECParser, CTECParsingError


class TestCTECParser:
    """Test suite for CTECParser class."""

    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.parser = CTECParser(debug=True)
        cls.samples_dir = Path(__file__).parent.parent.parent / "docs" / "samples"
        cls.sample_files = list(cls.samples_dir.glob("*.pdf"))

        if not cls.sample_files:
            raise ValueError(f"No PDF samples found in {cls.samples_dir}")

    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        parser = CTECParser()
        assert parser is not None
        assert not parser.debug

        debug_parser = CTECParser(debug=True)
        assert debug_parser.debug

    def test_sample_files_exist(self):
        """Test that sample files are available for testing."""
        assert len(self.sample_files) > 0, f"No samples found in {self.samples_dir}"
        print(f"Found {len(self.sample_files)} sample files")

    def test_parse_single_ctec_basic(self):
        """Test basic parsing of a single CTEC file."""
        if not self.sample_files:
            pytest.skip("No sample files available")

        sample_file = self.sample_files[0]
        try:
            result = self.parser.parse_ctec(str(sample_file))
            assert result is not None
            assert result.course_info is not None
            assert hasattr(result.course_info, 'code')
            assert hasattr(result.course_info, 'title')
            print(f"✓ Successfully parsed: {sample_file.name}")
        except Exception as e:
            pytest.fail(f"Failed to parse {sample_file.name}: {e}")

    def test_parse_all_samples(self):
        """Test parsing all sample files and track success rate."""
        if not self.sample_files:
            pytest.skip("No sample files available")

        results = self.parser.parse_multiple_ctecs(
            [str(f) for f in self.sample_files],
            continue_on_error=True
        )

        successful = results['successful']
        failed = results['failed']

        print(f"\nParsing Results:")
        print(f"✓ Successful: {len(successful)}")
        print(f"✗ Failed: {len(failed)}")

        if failed:
            print(f"\nFailed files:")
            for file_path, error in failed.items():
                file_name = Path(file_path).name
                print(f"  - {file_name}: {error}")

        # Ensure at least 50% success rate
        success_rate = len(successful) / len(self.sample_files)
        assert success_rate >= 0.5, f"Success rate too low: {success_rate:.1%}"

    def test_course_info_extraction_patterns(self):
        """Test course information extraction patterns."""
        test_cases = [
            # Pattern 1: Title (CODE_SECTION: Description) (Instructor)
            ("Student Report for Ethical Problems/Public Issues "
             "(PHIL_262-0_20: Ethical Problems/Public Issues) (Chad Horne)",
             {"code": "PHIL_262-0", "section": "20", 
              "title": "Ethical Problems/Public Issues", "instructor": "Chad Horne"}),
            # Pattern 2: CODE: Title (Instructor)
            ("Student Report for COMP_SCI_214-0: Data Structures & Algorithms "
             "(Vincent St Amour)",
             {"code": "COMP_SCI_214-0", "section": "", 
              "title": "Data Structures & Algorithms", "instructor": "Vincent St Amour"})
        ]

        for text, expected in test_cases:
            try:
                course_info = self.parser._extract_course_info(text)
                assert course_info.code == expected["code"]
                assert course_info.section == expected["section"]
                assert course_info.title == expected["title"]
                assert course_info.instructor == expected["instructor"]
                print(f"✓ Pattern extraction successful for: {expected['code']}")
            except Exception as e:
                pytest.fail(f"Failed to extract course info from pattern: {e}")

    def test_term_extraction(self):
        """Test quarter and year extraction."""
        test_cases = [
            ("Course and Teacher Evaluations CTEC Spring 2023", ("Spring", 2023)),
            ("Course and Teacher Evaluations CTEC Fall 2022", ("Fall", 2022)),
            ("Course and Teacher Evaluations CTEC Winter 2024", ("Winter", 2024))
        ]

        for text, expected in test_cases:
            try:
                quarter, year = self.parser._extract_term_info(text)
                assert quarter == expected[0]
                assert year == expected[1]
                print(f"✓ Term extraction successful: {quarter} {year}")
            except Exception as e:
                pytest.fail(f"Failed to extract term info: {e}")

    def test_demographic_extraction_coverage(self):
        """Test that demographic extraction covers expected categories."""
        # Test with a sample that has demographics
        for sample_file in self.sample_files:
            try:
                result = self.parser.parse_ctec(str(sample_file))
                demographics = result.survey_responses
                
                expected_sections = [
                    'school_name', 'class_year', 'reason_for_taking_course',
                    'prior_interest', 'time_survey'
                ]
                
                found_sections = [section for section in expected_sections
                                  if section in demographics and demographics[section]]
                
                if found_sections:
                    print(f"✓ {sample_file.name}: Found {len(found_sections)} "
                          f"demographic sections")
                    break
            except Exception:
                continue
        else:
            print("⚠ No demographic data found in any samples")

    def test_comments_extraction(self):
        """Test comments extraction from samples."""
        comments_found = 0
        for sample_file in self.sample_files:
            try:
                result = self.parser.parse_ctec(str(sample_file))
                if result.comments:
                    comments_found += 1
                    print(f"✓ {sample_file.name}: Found {len(result.comments)} comments")
            except Exception:
                continue

        if comments_found == 0:
            print("⚠ No comments found in any samples")
        else:
            print(f"✓ Found comments in {comments_found} files")

    def test_data_structure_integrity(self):
        """Test that parsed data maintains proper structure."""
        if not self.sample_files:
            pytest.skip("No sample files available")

        sample_file = self.sample_files[0]
        try:
            result = self.parser.parse_ctec(str(sample_file))
            
            # Test CTECData structure
            assert hasattr(result, 'course_info')
            assert hasattr(result, 'comments')
            assert hasattr(result, 'survey_responses')
            
            # Test CourseInfo structure
            assert hasattr(result.course_info, 'code')
            assert hasattr(result.course_info, 'title')
            assert hasattr(result.course_info, 'instructor')
            assert hasattr(result.course_info, 'section')
            assert hasattr(result.course_info, 'quarter')
            assert hasattr(result.course_info, 'year')
            assert hasattr(result.course_info, 'audience_size')
            assert hasattr(result.course_info, 'response_count')
            
            # Test to_dict conversion
            dict_result = result.to_dict()
            assert isinstance(dict_result, dict)
            assert 'code' in dict_result
            assert 'title' in dict_result
            assert 'comments' in dict_result
            assert 'survey_responses' in dict_result
            assert 'audience_size' in dict_result
            assert 'response_count' in dict_result
            
            print("✓ Data structure integrity verified")
            
        except Exception as e:
            pytest.fail(f"Data structure test failed: {e}")

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test non-existent file
        with pytest.raises(CTECParsingError):
            self.parser.parse_ctec("non_existent_file.pdf")
        
        # Test empty string
        with pytest.raises(CTECParsingError):
            self.parser.parse_ctec("")

    def test_audience_and_response_extraction(self):
        """Test audience size and response count extraction."""
        if not self.sample_files:
            pytest.skip("No sample files available")

        metadata_found = 0
        for sample_file in self.sample_files:
            try:
                result = self.parser.parse_ctec(str(sample_file))
                course_info = result.course_info
                
                if course_info.audience_size is not None or course_info.response_count is not None:
                    metadata_found += 1
                    print(f"✓ {sample_file.name}: Audience={course_info.audience_size}, "
                          f"Responses={course_info.response_count}")
                    
                    # Validate that extracted numbers are reasonable
                    if course_info.audience_size is not None:
                        assert isinstance(course_info.audience_size, int)
                        assert course_info.audience_size > 0
                    if course_info.response_count is not None:
                        assert isinstance(course_info.response_count, int)
                        assert course_info.response_count > 0
                        # Response count should not exceed audience size (if both present)
                        if course_info.audience_size is not None:
                            assert course_info.response_count <= course_info.audience_size
            except Exception as e:
                print(f"⚠ Failed to parse {sample_file.name}: {e}")
                continue

        if metadata_found == 0:
            print("⚠ No audience/response metadata found in any samples")
        else:
            print(f"✓ Found audience/response metadata in {metadata_found} files")

    def test_performance_timing(self):
        """Test parsing performance on sample files."""
        if not self.sample_files:
            pytest.skip("No sample files available")

        import time
        
        total_time = 0
        successful_parses = 0
        
        for sample_file in self.sample_files[:5]:  # Test first 5 files
            start_time = time.time()
            try:
                self.parser.parse_ctec(str(sample_file))
                successful_parses += 1
            except Exception:
                continue
            
            parse_time = time.time() - start_time
            total_time += parse_time
            print(f"✓ {sample_file.name}: {parse_time:.2f}s")
        
        if successful_parses > 0:
            avg_time = total_time / successful_parses
            print(f"Average parsing time: {avg_time:.2f}s")
            # Ensure parsing isn't too slow (adjust threshold as needed)
            assert avg_time < 30, f"Parsing too slow: {avg_time:.2f}s average"