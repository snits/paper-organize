# ABOUTME: Tests for PDF metadata extraction functionality
# ABOUTME: Covers PaperMetadata class and extraction functions
# SPDX-License-Identifier: MIT

import tempfile
from unittest.mock import MagicMock, patch

from paperorganize.metadata import (
    PaperMetadata,
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

    @patch("paperorganize.metadata.PdfReader")
    def test_extract_handles_missing_file(self, mock_pdf_reader: MagicMock) -> None:
        """Test graceful handling of missing PDF file."""
        mock_pdf_reader.side_effect = FileNotFoundError("File not found")

        result = extract_pdf_metadata("/nonexistent/file.pdf")

        # Should return empty metadata rather than raising exception
        assert result.title is None
        assert result.authors == []
        assert result.doi is None
        assert result.arxiv_id is None
        assert result.year is None

    @patch("paperorganize.metadata.PdfReader")
    def test_extract_handles_corrupted_pdf(self, mock_pdf_reader: MagicMock) -> None:
        """Test graceful handling of corrupted PDF file."""
        mock_pdf_reader.side_effect = Exception("PDF parsing error")

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

    def test_generate_filename_complete_metadata(self) -> None:
        """Test filename generation with complete metadata."""
        metadata = PaperMetadata(
            title="Machine Learning for Natural Language Processing",
            authors=["John Smith", "Jane Doe"],
            year=TEST_YEAR_2024,
        )

        result = generate_filename(metadata, "fallback.pdf")
        assert (
            result == "Smith_2024_Machine_Learning_for_Natural_Language_Processing.pdf"
        )

    def test_generate_filename_no_author(self) -> None:
        """Test filename generation without author information."""
        metadata = PaperMetadata(
            title="Deep Learning Techniques", authors=[], year=TEST_YEAR_2023
        )

        result = generate_filename(metadata, "fallback.pdf")
        assert result == "2023_Deep_Learning_Techniques.pdf"

    def test_generate_filename_no_year(self) -> None:
        """Test filename generation without year information."""
        metadata = PaperMetadata(
            title="Computer Vision Applications",
            authors=["Alice Johnson"],
            year=None,
        )

        result = generate_filename(metadata, "fallback.pdf")
        assert result == "Johnson_Computer_Vision_Applications.pdf"

    def test_generate_filename_title_only(self) -> None:
        """Test filename generation with title only."""
        metadata = PaperMetadata(
            title="Artificial Intelligence Overview", authors=[], year=None
        )

        result = generate_filename(metadata, "fallback.pdf")
        assert result == "Artificial_Intelligence_Overview.pdf"

    def test_generate_filename_no_metadata(self) -> None:
        """Test filename generation with no useful metadata."""
        metadata = PaperMetadata(title=None, authors=[], year=None)

        result = generate_filename(metadata, "original_filename.pdf")
        assert result == "original_filename.pdf"

    def test_generate_filename_sanitization(self) -> None:
        """Test filename sanitization of special characters."""
        metadata = PaperMetadata(
            title="Test/File:Name*With?Special<Characters>",
            authors=["O'Connor", "Smith-Jones"],
            year=TEST_YEAR_2024,
        )

        result = generate_filename(metadata, "fallback.pdf")
        # Should sanitize special characters but preserve readability
        # Only first author's last name is used in filename
        assert "O_Connor" in result or "OConnor" in result
        assert "Test_File_Name_With_Special_Characters" in result

    def test_generate_filename_unicode_handling(self) -> None:
        """Test filename generation with Unicode characters."""
        metadata = PaperMetadata(
            title="Résumé of Machine Learning Techniques",
            authors=["José García", "François Müller"],
            year=TEST_YEAR_2024,
        )

        result = generate_filename(metadata, "fallback.pdf")
        # Should handle Unicode normalization
        assert result.endswith(".pdf")
        assert "Machine_Learning" in result

    def test_generate_filename_long_title_truncation(self) -> None:
        """Test filename truncation for very long titles."""
        metadata = PaperMetadata(
            title="This is an extremely long paper title that should be truncated because filesystem limits require reasonable filename lengths and this exceeds those limits significantly",
            authors=["Smith"],
            year=TEST_YEAR_2024,
        )

        result = generate_filename(metadata, "fallback.pdf")
        # Should be truncated but still readable
        assert len(result) <= MAX_FILENAME_LENGTH
        assert result.startswith("Smith_2024_")
        assert result.endswith(".pdf")

    def test_generate_filename_multiple_authors_uses_first(self) -> None:
        """Test that filename uses only the first author's last name."""
        metadata = PaperMetadata(
            title="Collaborative Research",
            authors=["John Smith", "Alice Johnson", "Bob Williams"],
            year=TEST_YEAR_2024,
        )

        result = generate_filename(metadata, "fallback.pdf")
        assert result == "Smith_2024_Collaborative_Research.pdf"

    def test_generate_filename_author_name_variants(self) -> None:
        """Test handling of various author name formats."""
        # Test single name
        metadata = PaperMetadata(
            title="Research Paper", authors=["Aristotle"], year=TEST_YEAR_2024
        )
        result = generate_filename(metadata, "fallback.pdf")
        assert result == "Aristotle_2024_Research_Paper.pdf"

        # Test name with multiple parts
        metadata = PaperMetadata(
            title="Research Paper",
            authors=["Jean-Claude Van Damme"],
            year=TEST_YEAR_2024,
        )
        result = generate_filename(metadata, "fallback.pdf")
        assert result == "Damme_2024_Research_Paper.pdf"


class TestYearExtraction:
    """Test year extraction from various sources."""

    def test_extract_year_from_title_parentheses(self) -> None:
        """Test year extraction from title with parentheses."""
        metadata = PaperMetadata()
        _extract_year_from_title("Machine Learning (2024) Overview", metadata)
        assert metadata.year == TEST_YEAR_2024

    def test_extract_year_from_title_brackets(self) -> None:
        """Test year extraction from title with brackets."""
        metadata = PaperMetadata()
        _extract_year_from_title("Deep Learning [2023] Techniques", metadata)
        assert metadata.year == TEST_YEAR_2023

    def test_extract_year_from_title_standalone(self) -> None:
        """Test year extraction from standalone year in title."""
        metadata = PaperMetadata()
        _extract_year_from_title("AI Research 2022 Advances", metadata)
        assert metadata.year == TEST_YEAR_2022

    def test_extract_year_from_title_multiple_years(self) -> None:
        """Test year extraction when multiple years are present."""
        metadata = PaperMetadata()
        # Should take the last year found as most likely to be publication year
        _extract_year_from_title("Study of 1990-2023 Trends (2024)", metadata)
        assert metadata.year == TEST_YEAR_2024

    def test_extract_year_from_title_invalid_year(self) -> None:
        """Test that invalid years are ignored."""
        metadata = PaperMetadata()
        _extract_year_from_title("Research Paper (1800) Old", metadata)
        assert metadata.year is None

    def test_extract_year_from_title_future_year(self) -> None:
        """Test that reasonable future years are accepted."""
        metadata = PaperMetadata()
        _extract_year_from_title("Future Research (2025) Predictions", metadata)
        # Should accept years up to MAX_YEAR_OFFSET years in the future
        if TEST_YEAR_2025 <= 2024 + 5:  # MAX_YEAR_OFFSET is 5
            assert metadata.year == TEST_YEAR_2025

    def test_extract_year_from_title_no_year(self) -> None:
        """Test handling of titles with no year information."""
        metadata = PaperMetadata()
        _extract_year_from_title("Machine Learning Overview", metadata)
        assert metadata.year is None

    def test_extract_year_from_title_preserves_existing(self) -> None:
        """Test that existing year is preserved if already set."""
        metadata = PaperMetadata(year=TEST_YEAR_2022)
        _extract_year_from_title("Recent Research (2023)", metadata)
        assert metadata.year == TEST_YEAR_2022
