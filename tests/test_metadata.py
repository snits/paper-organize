# ABOUTME: Tests for PDF metadata extraction functionality
# ABOUTME: Covers PaperMetadata class and extraction functions

import tempfile
from unittest.mock import MagicMock, patch

from paperdl.metadata import PaperMetadata, extract_pdf_metadata, generate_filename


class TestPaperMetadata:
    """Test PaperMetadata dataclass functionality."""

    def test_paper_metadata_creation(self) -> None:
        """Test creating PaperMetadata with various fields."""
        metadata = PaperMetadata(
            title="Machine Learning Fundamentals",
            authors=["John Doe", "Jane Smith"],
            doi="10.1234/example.doi",
            arxiv_id="2401.12345",
            year=2024
        )

        assert metadata.title == "Machine Learning Fundamentals"
        assert metadata.authors == ["John Doe", "Jane Smith"]
        assert metadata.doi == "10.1234/example.doi"
        assert metadata.arxiv_id == "2401.12345"
        assert metadata.year == 2024

    def test_paper_metadata_optional_fields(self) -> None:
        """Test PaperMetadata with only some fields populated."""
        metadata = PaperMetadata(
            title="Minimal Paper",
            authors=None,
            doi=None,
            arxiv_id=None,
            year=None
        )

        assert metadata.title == "Minimal Paper"
        assert metadata.authors == []  # Should be initialized by __post_init__
        assert metadata.doi is None
        assert metadata.arxiv_id is None
        assert metadata.year is None


class TestExtractPdfMetadata:
    """Test PDF metadata extraction functionality."""

    @patch("paperdl.metadata.PdfReader")
    def test_extract_from_pypdf_metadata(self, mock_pdf_reader: MagicMock) -> None:
        """Test successful extraction from PDF metadata using pypdf."""
        # Setup mock PDF with metadata
        mock_reader = MagicMock()
        mock_reader.metadata = {
            "/Title": "Test Paper Title",
            "/Author": "John Doe, Jane Smith",
            "/Creator": "LaTeX",
            "/Subject": "Machine Learning"
        }
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.title == "Test Paper Title"
        assert "John Doe" in result.authors
        assert "Jane Smith" in result.authors

    @patch("paperdl.metadata.pdf2doi.pdf2doi")
    @patch("paperdl.metadata.PdfReader")
    def test_extract_with_pdf2doi_fallback(self, mock_pdf_reader: MagicMock,
                                         mock_pdf2doi: MagicMock) -> None:
        """Test fallback to pdf2doi when pypdf metadata is insufficient."""
        # Setup pypdf with minimal metadata
        mock_reader = MagicMock()
        mock_reader.metadata = {}
        mock_pdf_reader.return_value = mock_reader

        # Setup pdf2doi with DOI result
        mock_pdf2doi.return_value = {
            "identifier": "10.1234/example.doi",
            "identifier_type": "doi"
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.doi == "10.1234/example.doi"
        mock_pdf2doi.assert_called_once_with(tmp_file.name)

    @patch("paperdl.metadata.pdf2doi.pdf2doi")
    @patch("paperdl.metadata.PdfReader")
    def test_extract_arxiv_id(self, mock_pdf_reader: MagicMock,
                             mock_pdf2doi: MagicMock) -> None:
        """Test extraction of arXiv identifier."""
        mock_reader = MagicMock()
        mock_reader.metadata = {}
        mock_pdf_reader.return_value = mock_reader

        mock_pdf2doi.return_value = {
            "identifier": "2401.12345",
            "identifier_type": "arxiv"
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extract_pdf_metadata(tmp_file.name)

        assert result.arxiv_id == "2401.12345"

    @patch("paperdl.metadata.pdf2doi.pdf2doi")
    @patch("paperdl.metadata.PdfReader")
    def test_extract_handles_missing_file(self, mock_pdf_reader: MagicMock,
                                        mock_pdf2doi: MagicMock) -> None:
        """Test graceful handling of missing PDF file."""
        mock_pdf_reader.side_effect = FileNotFoundError("File not found")

        result = extract_pdf_metadata("/nonexistent/file.pdf")

        # Should return empty metadata rather than raising exception
        assert result.title is None
        assert result.authors == []
        assert result.doi is None
        assert result.arxiv_id is None
        assert result.year is None

    @patch("paperdl.metadata.pdf2doi.pdf2doi")
    @patch("paperdl.metadata.PdfReader")
    def test_extract_handles_corrupted_pdf(self, mock_pdf_reader: MagicMock,
                                         mock_pdf2doi: MagicMock) -> None:
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
            year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        # Expected format: FirstAuthor_Year_Title.pdf
        assert result == "Doe_2024_Machine_Learning_A_Comprehensive_Survey.pdf"

    def test_generate_filename_multiple_authors(self) -> None:
        """Test filename generation with multiple authors."""
        metadata = PaperMetadata(
            title="Deep Neural Networks",
            authors=["Alice Johnson", "Bob Wilson", "Carol Davis"],
            year=2023
        )

        result = generate_filename(metadata, "original.pdf")

        # Should use first author only
        assert result == "Johnson_2023_Deep_Neural_Networks.pdf"

    def test_generate_filename_special_characters(self) -> None:
        """Test filename sanitization with special characters."""
        metadata = PaperMetadata(
            title="AI & ML: The Future/Present?",
            authors=["Dr. María José"],
            year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        # Special characters should be sanitized
        assert result == "Jose_2024_AI_ML_The_Future_Present.pdf"

    def test_generate_filename_long_title(self) -> None:
        """Test title truncation for very long titles."""
        metadata = PaperMetadata(
            title="A Very Long Title That Exceeds Normal Filesystem Limits And Should Be Truncated To Prevent Issues With File Operations",
            authors=["John Smith"],
            year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        # Should truncate title but keep readable
        assert len(result) <= 100  # Reasonable filename length
        assert result.startswith("Smith_2024_A_Very_Long_Title")
        assert result.endswith(".pdf")

    def test_generate_filename_missing_year(self) -> None:
        """Test filename generation when year is missing."""
        metadata = PaperMetadata(
            title="Recent Advances in AI",
            authors=["Jane Doe"],
            year=None
        )

        result = generate_filename(metadata, "original.pdf")

        # Should work without year
        assert result == "Doe_Recent_Advances_in_AI.pdf"

    def test_generate_filename_no_authors(self) -> None:
        """Test filename generation when authors are missing."""
        metadata = PaperMetadata(
            title="Anonymous Paper",
            authors=[],
            year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        # Should work without authors
        assert result == "2024_Anonymous_Paper.pdf"

    def test_generate_filename_minimal_metadata(self) -> None:
        """Test filename generation with only title."""
        metadata = PaperMetadata(
            title="Minimal Paper",
            authors=[],
            year=None
        )

        result = generate_filename(metadata, "original.pdf")

        assert result == "Minimal_Paper.pdf"

    def test_generate_filename_fallback_to_original(self) -> None:
        """Test fallback to original filename when metadata is insufficient."""
        metadata = PaperMetadata(
            title=None,
            authors=[],
            year=None
        )

        result = generate_filename(metadata, "research_paper.pdf")

        # Should fall back to original filename
        assert result == "research_paper.pdf"

    def test_generate_filename_preserve_extension(self) -> None:
        """Test that PDF extension is always preserved."""
        metadata = PaperMetadata(
            title="Test Paper",
            authors=["Author"],
            year=2024
        )

        result = generate_filename(metadata, "document.pdf")

        assert result.endswith(".pdf")

    def test_generate_filename_no_spaces_in_output(self) -> None:
        """Test that generated filenames contain no spaces."""
        metadata = PaperMetadata(
            title="Title With Many Spaces",
            authors=["First Last"],
            year=2024
        )

        result = generate_filename(metadata, "original.pdf")

        assert " " not in result
        assert result == "Last_2024_Title_With_Many_Spaces.pdf"
