# ABOUTME: Tests for PDF metadata extraction functionality
# ABOUTME: Covers PaperMetadata class and extraction functions
# SPDX-License-Identifier: MIT

import tempfile
from unittest.mock import MagicMock, patch

from paperorganize.metadata import (
    PaperMetadata,
    _extract_authors_from_info,
    _extract_title_from_info,
    _extract_validation_info,
    _extract_year_from_info,
    _extract_year_from_title,
    extract_pdf_metadata,
    generate_filename,
)

# Test constants to avoid magic numbers
TEST_YEAR_2024 = 2024
TEST_YEAR_2023 = 2023
TEST_YEAR_2022 = 2022
TEST_YEAR_1950 = 1950
TEST_YEAR_2025 = 2025
MAX_FILENAME_LENGTH = 100


class TestPaperMetadata:
    """Test PaperMetadata dataclass functionality."""

    def test_paper_metadata_creation(self) -> None:
        """Test creating PaperMetadata with various fields."""
        metadata = PaperMetadata(
            title="Machine Learning Fundamentals",
            authors=["John Doe", "Jane Smith"],
            doi="10.1234/example.doi",
            arxiv_id="2401.12345",
            year=2024,
        )

        assert metadata.title == "Machine Learning Fundamentals"
        assert metadata.authors == ["John Doe", "Jane Smith"]
        assert metadata.doi == "10.1234/example.doi"
        assert metadata.arxiv_id == "2401.12345"
        assert metadata.year == TEST_YEAR_2024

    def test_paper_metadata_optional_fields(self) -> None:
        """Test PaperMetadata with only some fields populated."""
        metadata = PaperMetadata(
            title="Minimal Paper", authors=None, doi=None, arxiv_id=None, year=None
        )

        assert metadata.title == "Minimal Paper"
        assert metadata.authors == []  # Should be initialized by __post_init__
        assert metadata.doi is None
        assert metadata.arxiv_id is None
        assert metadata.year is None


class TestExtractPdfMetadata:
    """Test PDF metadata extraction functionality."""

    @patch("paperorganize.metadata.PdfReader")
    def test_extract_from_pypdf_metadata(self, mock_pdf_reader: MagicMock) -> None:
        """Test successful extraction from PDF metadata using pypdf."""
        # Setup mock PDF with metadata
        mock_reader = MagicMock()
        mock_reader.metadata = {
            "/Title": "Test Paper Title",
            "/Author": "John Doe, Jane Smith",
            "/Creator": "LaTeX",
            "/Subject": "Machine Learning",
        }
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.title == "Test Paper Title"
        assert result.authors is not None
        assert "John Doe" in result.authors
        assert "Jane Smith" in result.authors

    @patch("paperorganize.metadata.pdf2doi.pdf2doi")
    @patch("paperorganize.metadata.PdfReader")
    def test_extract_with_pdf2doi_fallback(
        self, mock_pdf_reader: MagicMock, mock_pdf2doi: MagicMock
    ) -> None:
        """Test fallback to pdf2doi when pypdf metadata is insufficient."""
        # Setup pypdf with minimal metadata
        mock_reader = MagicMock()
        mock_reader.metadata = {}
        mock_pdf_reader.return_value = mock_reader

        # Setup pdf2doi with DOI result
        mock_pdf2doi.return_value = {
            "identifier": "10.1234/example.doi",
            "identifier_type": "doi",
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.doi == "10.1234/example.doi"
        mock_pdf2doi.assert_called_once_with(tmp_file.name)

    @patch("paperorganize.metadata.pdf2doi.pdf2doi")
    @patch("paperorganize.metadata.PdfReader")
    def test_extract_arxiv_id(
        self, mock_pdf_reader: MagicMock, mock_pdf2doi: MagicMock
    ) -> None:
        """Test extraction of arXiv identifier."""
        mock_reader = MagicMock()
        mock_reader.metadata = {}
        mock_pdf_reader.return_value = mock_reader

        mock_pdf2doi.return_value = {
            "identifier": "2401.12345",
            "identifier_type": "arxiv",
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.arxiv_id == "2401.12345"

    @patch("paperorganize.metadata.pdf2doi.pdf2doi")
    @patch("paperorganize.metadata.PdfReader")
    def test_extract_handles_missing_file(
        self, mock_pdf_reader: MagicMock, _mock_pdf2doi: MagicMock
    ) -> None:
        """Test graceful handling of missing PDF file."""
        mock_pdf_reader.side_effect = FileNotFoundError("File not found")

        result = extract_pdf_metadata("/nonexistent/file.pdf")

        # Should return empty metadata rather than raising exception
        assert result.title is None
        assert result.authors == []
        assert result.doi is None
        assert result.arxiv_id is None
        assert result.year is None

    @patch("paperorganize.metadata.pdf2doi.pdf2doi")
    @patch("paperorganize.metadata.PdfReader")
    def test_extract_handles_corrupted_pdf(
        self, mock_pdf_reader: MagicMock, mock_pdf2doi: MagicMock
    ) -> None:
        """Test graceful handling of corrupted PDF file."""
        mock_pdf_reader.side_effect = Exception("PDF parsing error")
        mock_pdf2doi.side_effect = Exception("pdf2doi error")

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        # Should return empty metadata rather than raising exception
        assert result.title is None
        assert result.authors == []
        assert result.doi is None
        assert result.arxiv_id is None
        assert result.year is None


class TestGenerateFilename:
    """Test filename generation from metadata."""

    def test_generate_filename_full_metadata(self) -> None:
        """Test filename generation with complete metadata."""
        metadata = PaperMetadata(
            title="Machine Learning: A Comprehensive Survey",
            authors=["John Doe", "Jane Smith"],
            year=2024,
        )

        result = generate_filename(metadata, "original.pdf")

        # Expected format: FirstAuthor_Year_Title.pdf
        assert result == "Doe_2024_Machine_Learning_A_Comprehensive_Survey.pdf"

    def test_generate_filename_multiple_authors(self) -> None:
        """Test filename generation with multiple authors."""
        metadata = PaperMetadata(
            title="Deep Neural Networks",
            authors=["Alice Johnson", "Bob Wilson", "Carol Davis"],
            year=2023,
        )

        result = generate_filename(metadata, "original.pdf")

        # Should use first author only
        assert result == "Johnson_2023_Deep_Neural_Networks.pdf"

    def test_generate_filename_special_characters(self) -> None:
        """Test filename sanitization with special characters."""
        metadata = PaperMetadata(
            title="AI & ML: The Future/Present?", authors=["Dr. María José"], year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        # Special characters should be sanitized
        assert result == "Jose_2024_AI_ML_The_Future_Present.pdf"

    def test_generate_filename_long_title(self) -> None:
        """Test title truncation for very long titles."""
        metadata = PaperMetadata(
            title="A Very Long Title That Exceeds Normal Filesystem Limits And Should Be Truncated To Prevent Issues With File Operations",
            authors=["John Smith"],
            year=2024,
        )

        result = generate_filename(metadata, "original.pdf")

        # Should truncate title but keep readable
        assert len(result) <= MAX_FILENAME_LENGTH  # Reasonable filename length
        assert result.startswith("Smith_2024_A_Very_Long_Title")
        assert result.endswith(".pdf")

    def test_generate_filename_missing_year(self) -> None:
        """Test filename generation when year is missing."""
        metadata = PaperMetadata(
            title="Recent Advances in AI", authors=["Jane Doe"], year=None
        )

        result = generate_filename(metadata, "original.pdf")

        # Should work without year
        assert result == "Doe_Recent_Advances_in_AI.pdf"

    def test_generate_filename_no_authors(self) -> None:
        """Test filename generation when authors are missing."""
        metadata = PaperMetadata(title="Anonymous Paper", authors=[], year=2024)

        result = generate_filename(metadata, "original.pdf")

        # Should work without authors
        assert result == "2024_Anonymous_Paper.pdf"

    def test_generate_filename_minimal_metadata(self) -> None:
        """Test filename generation with only title."""
        metadata = PaperMetadata(title="Minimal Paper", authors=[], year=None)

        result = generate_filename(metadata, "original.pdf")

        assert result == "Minimal_Paper.pdf"

    def test_generate_filename_fallback_to_original(self) -> None:
        """Test fallback to original filename when metadata is insufficient."""
        metadata = PaperMetadata(title=None, authors=[], year=None)

        result = generate_filename(metadata, "research_paper.pdf")

        # Should fall back to original filename
        assert result == "research_paper.pdf"

    def test_generate_filename_preserve_extension(self) -> None:
        """Test that PDF extension is always preserved."""
        metadata = PaperMetadata(title="Test Paper", authors=["Author"], year=2024)

        result = generate_filename(metadata, "document.pdf")

        assert result.endswith(".pdf")

    def test_generate_filename_no_spaces_in_output(self) -> None:
        """Test that generated filenames contain no spaces."""
        metadata = PaperMetadata(
            title="Title With Many Spaces", authors=["First Last"], year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        assert " " not in result
        assert result == "Last_2024_Title_With_Many_Spaces.pdf"


class TestYearExtraction:
    """Test year extraction from titles and PDF metadata."""

    def test_extract_year_from_title_parentheses(self) -> None:
        """Test year extraction from title with parentheses."""
        metadata = PaperMetadata(title="Machine Learning Survey (2024)")
        _extract_year_from_title("Machine Learning Survey (2024)", metadata)
        assert metadata.year == TEST_YEAR_2024

    def test_extract_year_from_title_brackets(self) -> None:
        """Test year extraction from title with brackets."""
        metadata = PaperMetadata(title="Deep Learning Advances [2023]")
        _extract_year_from_title("Deep Learning Advances [2023]", metadata)
        assert metadata.year == TEST_YEAR_2023

    def test_extract_year_from_title_standalone(self) -> None:
        """Test year extraction from standalone year in title."""
        metadata = PaperMetadata(title="AI Research 2022 Overview")
        _extract_year_from_title("AI Research 2022 Overview", metadata)
        assert metadata.year == TEST_YEAR_2022

    def test_extract_year_from_title_multiple_years(self) -> None:
        """Test year extraction when multiple years present - should take last."""
        metadata = PaperMetadata(title="Comparing 2020 vs 2024 ML Methods")
        _extract_year_from_title("Comparing 2020 vs 2024 ML Methods", metadata)
        assert metadata.year == TEST_YEAR_2024

    def test_extract_year_from_title_invalid_range(self) -> None:
        """Test year extraction rejects years outside valid range."""
        metadata = PaperMetadata(title="Historical Analysis 1850-1950")
        _extract_year_from_title("Historical Analysis 1850-1950", metadata)
        # Should reject 1850 as too old, accept 1950 as valid
        assert metadata.year == TEST_YEAR_1950

    def test_extract_year_from_title_no_year(self) -> None:
        """Test year extraction when no year found in title."""
        metadata = PaperMetadata(title="Modern Machine Learning Techniques")
        _extract_year_from_title("Modern Machine Learning Techniques", metadata)
        assert metadata.year is None

    @patch("paperorganize.metadata.PdfReader")
    def test_extract_year_from_pdf_creation_date(
        self, mock_pdf_reader: MagicMock
    ) -> None:
        """Test year extraction from PDF creation date."""
        mock_reader = MagicMock()
        mock_reader.metadata = {
            "/Title": "Test Paper",
            "/CreationDate": "D:20240315142530+00'00'",
        }
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.year == TEST_YEAR_2024

    @patch("paperorganize.metadata.PdfReader")
    def test_extract_year_from_pdf_mod_date_fallback(
        self, mock_pdf_reader: MagicMock
    ) -> None:
        """Test year extraction from PDF modification date as fallback."""
        mock_reader = MagicMock()
        mock_reader.metadata = {
            "/Title": "Test Paper",
            "/ModDate": "D:20230815142530+00'00'",
        }
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.year == TEST_YEAR_2023

    @patch("paperorganize.metadata.PdfReader")
    def test_extract_year_from_title_fallback(self, mock_pdf_reader: MagicMock) -> None:
        """Test year extraction from title when PDF metadata has no dates."""
        mock_reader = MagicMock()
        mock_reader.metadata = {"/Title": "Machine Learning Research (2025)"}
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.year == TEST_YEAR_2025


class TestValidationInfoExtraction:
    """Test validation_info parsing functions from pdf2doi."""

    def test_extract_validation_info_complete(self) -> None:
        """Test extracting complete metadata from validation_info JSON."""
        validation_info = """{
            "title": "Mastering Chess and Shogi by Self-Play",
            "author": [
                {"family": "Silver", "given": "David"},
                {"family": "Hubert", "given": "Thomas"}
            ],
            "issued": {"date-parts": [[2017]]}
        }"""

        metadata = PaperMetadata()
        _extract_validation_info(validation_info, metadata)

        assert metadata.title == "Mastering Chess and Shogi by Self-Play"
        assert metadata.authors == ["David Silver", "Thomas Hubert"]
        assert metadata.year == 2017

    def test_extract_validation_info_malformed_json(self) -> None:
        """Test handling of malformed JSON in validation_info."""
        metadata = PaperMetadata()

        # Should not raise exception with invalid JSON
        _extract_validation_info("invalid json {", metadata)

        # Metadata should remain unchanged
        assert metadata.title is None
        assert metadata.authors == []
        assert metadata.year is None

    def test_extract_validation_info_empty_string(self) -> None:
        """Test handling of empty validation_info."""
        metadata = PaperMetadata()
        _extract_validation_info("", metadata)

        assert metadata.title is None
        assert metadata.authors == []
        assert metadata.year is None

    def test_extract_validation_info_missing_fields(self) -> None:
        """Test validation_info with missing fields."""
        validation_info = '{"other_field": "value"}'
        metadata = PaperMetadata()

        _extract_validation_info(validation_info, metadata)

        assert metadata.title is None
        assert metadata.authors == []
        assert metadata.year is None

    def test_extract_validation_info_preserves_existing(self) -> None:
        """Test that existing metadata is not overwritten."""
        validation_info = """{
            "title": "New Title",
            "author": [{"family": "New", "given": "Author"}],
            "issued": {"date-parts": [[2023]]}
        }"""

        # Create metadata with existing values
        metadata = PaperMetadata(
            title="Existing Title", authors=["Existing Author"], year=2022
        )

        _extract_validation_info(validation_info, metadata)

        # Existing values should be preserved
        assert metadata.title == "Existing Title"
        assert metadata.authors == ["Existing Author"]
        assert metadata.year == 2022


class TestTitleExtraction:
    """Test title extraction from validation_info."""

    def test_extract_title_from_info_success(self) -> None:
        """Test successful title extraction."""
        info = {"title": "  Deep Learning Fundamentals  "}
        metadata = PaperMetadata()

        _extract_title_from_info(info, metadata)

        assert metadata.title == "Deep Learning Fundamentals"  # Stripped

    def test_extract_title_from_info_no_title(self) -> None:
        """Test when title field is missing."""
        info = {"other_field": "value"}
        metadata = PaperMetadata()

        _extract_title_from_info(info, metadata)

        assert metadata.title is None

    def test_extract_title_from_info_empty_title(self) -> None:
        """Test when title field is empty."""
        info = {"title": ""}
        metadata = PaperMetadata()

        _extract_title_from_info(info, metadata)

        assert metadata.title is None

    def test_extract_title_from_info_preserves_existing(self) -> None:
        """Test that existing title is not overwritten."""
        info = {"title": "New Title"}
        metadata = PaperMetadata(title="Existing Title")

        _extract_title_from_info(info, metadata)

        assert metadata.title == "Existing Title"


class TestAuthorsExtraction:
    """Test author extraction from validation_info."""

    def test_extract_authors_structured_format(self) -> None:
        """Test extraction of authors in structured format."""
        info = {
            "author": [
                {"family": "Doe", "given": "John"},
                {"family": "Smith", "given": "Jane"},
                {"family": "Johnson"},  # Only family name
            ]
        }
        metadata = PaperMetadata()

        _extract_authors_from_info(info, metadata)

        assert metadata.authors == ["John Doe", "Jane Smith", "Johnson"]

    def test_extract_authors_string_format(self) -> None:
        """Test extraction when authors are strings."""
        info = {"author": ["John Doe", "Jane Smith"]}
        metadata = PaperMetadata()

        _extract_authors_from_info(info, metadata)

        assert metadata.authors == ["John Doe", "Jane Smith"]

    def test_extract_authors_mixed_format(self) -> None:
        """Test extraction with mixed author formats."""
        info = {
            "author": [
                {"family": "Doe", "given": "John"},
                "Jane Smith",
                {"family": "Johnson", "given": ""},  # Empty given name
                {"given": "Bob"},  # Only given name - ignored by implementation
            ]
        }
        metadata = PaperMetadata()

        _extract_authors_from_info(info, metadata)

        # Only given name is ignored (no family name)
        assert metadata.authors == ["John Doe", "Jane Smith", "Johnson"]

    def test_extract_authors_no_author_field(self) -> None:
        """Test when author field is missing."""
        info = {"title": "Some Title"}
        metadata = PaperMetadata()

        _extract_authors_from_info(info, metadata)

        assert metadata.authors == []

    def test_extract_authors_empty_author_list(self) -> None:
        """Test when author field is empty list."""
        info: dict[str, list[str]] = {"author": []}
        metadata = PaperMetadata()

        _extract_authors_from_info(info, metadata)

        assert metadata.authors == []

    def test_extract_authors_preserves_existing(self) -> None:
        """Test that existing authors are not overwritten."""
        info = {"author": [{"family": "New", "given": "Author"}]}
        metadata = PaperMetadata(authors=["Existing Author"])

        _extract_authors_from_info(info, metadata)

        assert metadata.authors == ["Existing Author"]

    def test_extract_authors_filters_empty_names(self) -> None:
        """Test that empty author names are filtered out."""
        info = {
            "author": [
                {"family": "Doe", "given": "John"},
                {"family": "", "given": ""},  # Empty
                "  ",  # Whitespace only
                {"family": "Smith", "given": "Jane"},
            ]
        }
        metadata = PaperMetadata()

        _extract_authors_from_info(info, metadata)

        assert metadata.authors == ["John Doe", "Jane Smith"]


class TestYearExtractionFromInfo:
    """Test year extraction from validation_info."""

    def test_extract_year_from_info_success(self) -> None:
        """Test successful year extraction."""
        info = {"issued": {"date-parts": [[2023]]}}
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year == 2023

    def test_extract_year_from_info_no_issued(self) -> None:
        """Test when issued field is missing."""
        info = {"title": "Some Title"}
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year is None

    def test_extract_year_from_info_no_date_parts(self) -> None:
        """Test when date-parts field is missing."""
        info = {"issued": {"other_field": "value"}}
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year is None

    def test_extract_year_from_info_empty_date_parts(self) -> None:
        """Test when date-parts is empty."""
        info: dict[str, dict[str, list[list[int]]]] = {"issued": {"date-parts": []}}
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year is None

    def test_extract_year_from_info_malformed_date_parts(self) -> None:
        """Test malformed date-parts structure."""
        info: dict[str, dict[str, list[list[int]]]] = {
            "issued": {"date-parts": [[]]}
        }  # Empty inner array
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year is None

    def test_extract_year_from_info_invalid_year(self) -> None:
        """Test with invalid year value."""
        info = {"issued": {"date-parts": [[1800]]}}  # Too old
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year is None

    def test_extract_year_from_info_string_year(self) -> None:
        """Test when year is a string instead of int."""
        info = {"issued": {"date-parts": [["2023"]]}}
        metadata = PaperMetadata()

        _extract_year_from_info(info, metadata)

        assert metadata.year is None  # Should reject non-int

    def test_extract_year_from_info_preserves_existing(self) -> None:
        """Test that existing year is not overwritten."""
        info = {"issued": {"date-parts": [[2023]]}}
        metadata = PaperMetadata(year=2022)

        _extract_year_from_info(info, metadata)

        assert metadata.year == 2022


class TestPdf2doiCaseSensitivity:
    """Test case sensitivity fix for pdf2doi identifier_type."""

    @patch("paperorganize.metadata.pdf2doi")
    def test_pdf2doi_case_insensitive_doi(self, mock_pdf2doi: MagicMock) -> None:
        """Test that DOI is extracted regardless of case."""
        # Mock pdf2doi to return "DOI" (uppercase) as it actually does
        mock_pdf2doi.pdf2doi.return_value = {
            "identifier": "10.48550/arxiv.1234.5678",
            "identifier_type": "DOI",  # Uppercase as returned by real pdf2doi
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.doi == "10.48550/arxiv.1234.5678"

    @patch("paperorganize.metadata.pdf2doi")
    def test_pdf2doi_case_insensitive_arxiv(self, mock_pdf2doi: MagicMock) -> None:
        """Test that arXiv ID is extracted regardless of case."""
        mock_pdf2doi.pdf2doi.return_value = {
            "identifier": "1234.5678",
            "identifier_type": "ARXIV",  # Uppercase
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.arxiv_id == "1234.5678"

    @patch("paperorganize.metadata.pdf2doi")
    def test_pdf2doi_mixed_case_handling(self, mock_pdf2doi: MagicMock) -> None:
        """Test handling of mixed case identifier types."""
        mock_pdf2doi.pdf2doi.return_value = {
            "identifier": "10.1234/test",
            "identifier_type": "DoI",  # Mixed case
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.doi == "10.1234/test"


class TestPdf2doiRichMetadata:
    """Test extraction of rich metadata from pdf2doi validation_info."""

    @patch("paperorganize.metadata.pdf2doi")
    def test_pdf2doi_with_validation_info(self, mock_pdf2doi: MagicMock) -> None:
        """Test extraction when pdf2doi provides validation_info."""
        validation_info = """{
            "title": "Test Paper Title",
            "author": [
                {"family": "Test", "given": "Author"}
            ],
            "issued": {"date-parts": [[2023]]},
            "DOI": "10.1234/test"
        }"""

        mock_pdf2doi.pdf2doi.return_value = {
            "identifier": "10.1234/test",
            "identifier_type": "DOI",
            "validation_info": validation_info,
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.title == "Test Paper Title"
        assert result.authors == ["Author Test"]
        assert result.year == 2023
        assert result.doi == "10.1234/test"

    @patch("paperorganize.metadata.pdf2doi")
    def test_pdf2doi_validation_info_error_handling(
        self, mock_pdf2doi: MagicMock
    ) -> None:
        """Test graceful handling of malformed validation_info."""
        mock_pdf2doi.pdf2doi.return_value = {
            "identifier": "10.1234/test",
            "identifier_type": "DOI",
            "validation_info": "invalid json {{",
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        # Should still extract DOI but not crash on bad validation_info
        assert result.doi == "10.1234/test"
        assert result.title is None
        assert result.authors == []
