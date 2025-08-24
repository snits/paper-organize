# ABOUTME: Tests for enhanced metadata extraction components
# ABOUTME: Covers text extractors, pattern matchers, and orchestration layer
# SPDX-License-Identifier: MIT

import tempfile
import time
from unittest.mock import MagicMock, patch

from paperorganize.metadata import PaperMetadata
from paperorganize.metadata_extraction.api_clients import ArxivClient, CrossRefClient
from paperorganize.metadata_extraction.metadata_enricher import (
    EnhancedMetadataExtractor,
)
from paperorganize.metadata_extraction.pattern_matchers import (
    IdentifierMatch,
    _is_valid_arxiv_format,
    find_arxiv_patterns,
    find_doi_patterns,
)
from paperorganize.metadata_extraction.text_extractors import (
    PdfPlumberExtractor,
    PyPDFExtractor,
)


class TestPdfPlumberExtractor:
    """Test pdfplumber-based text extraction."""

    @patch("pdfplumber.open")
    def test_extract_text_success(self, mock_pdfplumber_open: MagicMock) -> None:
        """Test successful text extraction with pdfplumber."""
        extractor = PdfPlumberExtractor()

        # Setup mock PDF with pages
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text with DOI: 10.1234/example"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 additional content"

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extractor.extract_text(tmp_file.name)

        assert "Page 1 text with DOI: 10.1234/example" in result
        assert "Page 2 additional content" in result

    @patch("pdfplumber.open")
    def test_extract_text_early_exit_optimization(
        self, mock_pdfplumber_open: MagicMock
    ) -> None:
        """Test early exit when enough text is extracted."""
        extractor = PdfPlumberExtractor()

        # Create long text that exceeds 5000 characters
        long_text = "A" * 6000  # Exceeds the 5000 char limit

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = long_text
        mock_pdf.pages = [mock_page] * 10  # 10 pages, but should stop early
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extractor.extract_text(tmp_file.name)

        assert long_text in result
        # Should have called extract_text only once due to early exit
        mock_page.extract_text.assert_called_once()


class TestPyPDFExtractor:
    """Test pypdf-based text extraction."""

    @patch("pypdf.PdfReader")
    def test_extract_text_success(self, mock_pdf_reader: MagicMock) -> None:
        """Test successful text extraction with pypdf."""
        extractor = PyPDFExtractor()

        # Setup mock PDF reader
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "PyPDF extracted text"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Second page content"

        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            result = extractor.extract_text(tmp_file.name)

        assert "PyPDF extracted text" in result
        assert "Second page content" in result


class TestPatternMatchers:
    """Test DOI and arXiv pattern matching."""

    def test_find_doi_patterns_standard_format(self) -> None:
        """Test DOI pattern matching with standard format."""
        text = "This paper has DOI: 10.1234/example.doi and other content."

        matches = find_doi_patterns(text)

        assert len(matches) == 1
        assert matches[0].identifier == "10.1234/example.doi"
        assert matches[0].identifier_type == "doi"
        assert matches[0].confidence > 0.8

    def test_find_doi_patterns_url_format(self) -> None:
        """Test DOI pattern matching with URL format."""
        text = "Available at https://doi.org/10.5678/another.example for details."

        matches = find_doi_patterns(text)

        assert len(matches) == 1
        assert matches[0].identifier == "10.5678/another.example"
        assert matches[0].identifier_type == "doi"

    def test_find_doi_patterns_no_matches(self) -> None:
        """Test DOI pattern matching with no DOI present."""
        text = "This text contains no DOI identifiers at all."

        matches = find_doi_patterns(text)

        assert len(matches) == 0

    def test_find_arxiv_patterns_new_format(self) -> None:
        """Test arXiv pattern matching with new format."""
        text = "arXiv:2401.12345v1 contains the research details."

        matches = find_arxiv_patterns(text)

        assert len(matches) == 1
        assert matches[0].identifier == "2401.12345v1"
        assert matches[0].identifier_type == "arxiv"
        assert matches[0].confidence > 0.9

    def test_find_arxiv_patterns_old_format(self) -> None:
        """Test arXiv pattern matching with old format."""
        text = "See cs.AI/0123456 for the original paper."

        matches = find_arxiv_patterns(text)

        assert len(matches) == 1
        assert matches[0].identifier == "cs.AI/0123456"
        assert matches[0].identifier_type == "arxiv"

    def test_find_arxiv_patterns_url_format(self) -> None:
        """Test arXiv pattern matching with URL format."""
        text = "https://arxiv.org/abs/2401.12345 shows the results."

        matches = find_arxiv_patterns(text)

        assert len(matches) == 1
        assert matches[0].identifier == "2401.12345"
        assert matches[0].identifier_type == "arxiv"

    def test_is_valid_arxiv_format_new_format(self) -> None:
        """Test arXiv format validation for new format."""
        assert _is_valid_arxiv_format("2401.12345") is True
        assert _is_valid_arxiv_format("2401.12345v1") is True
        assert _is_valid_arxiv_format("1234.5678v10") is True

    def test_is_valid_arxiv_format_old_format(self) -> None:
        """Test arXiv format validation for old format."""
        assert _is_valid_arxiv_format("cs.AI/0123456") is True
        assert _is_valid_arxiv_format("math-ph/0234567") is True
        assert _is_valid_arxiv_format("hep-th/0345678") is True

    def test_is_valid_arxiv_format_invalid(self) -> None:
        """Test arXiv format validation rejects invalid formats."""
        assert _is_valid_arxiv_format("invalid") is False
        assert _is_valid_arxiv_format("123.456") is False  # Too short
        assert _is_valid_arxiv_format("not-arxiv/123") is False


class TestApiClients:
    """Test API client interfaces and implementations."""

    def test_arxiv_client_initialization(self) -> None:
        """Test ArxivClient can be initialized."""
        client = ArxivClient()
        assert client is not None
        assert client._min_request_interval == 3.0
        assert client._last_request_time == 0.0

    def test_crossref_client_initialization(self) -> None:
        """Test CrossRefClient can be initialized."""
        client = CrossRefClient()
        assert client is not None
        assert client._min_request_interval == 1.0
        assert client._base_url == "https://api.crossref.org/works/"

    @patch("time.sleep")
    def test_arxiv_client_rate_limiting(self, mock_sleep: MagicMock) -> None:
        """Test ArxivClient applies rate limiting."""
        client = ArxivClient()

        # Simulate recent request
        client._last_request_time = time.time() - 1.0  # 1 second ago

        # This should trigger rate limiting
        client._apply_rate_limit()

        # Should have slept for ~2 seconds (3.0 - 1.0)
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert 1.8 <= sleep_time <= 2.2  # Allow some timing variance

    @patch("time.sleep")
    def test_crossref_client_rate_limiting(self, mock_sleep: MagicMock) -> None:
        """Test CrossRefClient applies rate limiting."""
        client = CrossRefClient()

        # Simulate recent request
        client._last_request_time = time.time() - 0.5  # 0.5 seconds ago

        # This should trigger rate limiting
        client._apply_rate_limit()

        # Should have slept for ~0.5 seconds (1.0 - 0.5)
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert 0.3 <= sleep_time <= 0.7  # Allow some timing variance

    def test_arxiv_client_normalize_id(self) -> None:
        """Test ArxivClient normalizes IDs correctly."""
        client = ArxivClient()

        # Test various input formats
        assert client._normalize_arxiv_id("2401.12345") == "2401.12345"
        assert client._normalize_arxiv_id("arXiv:2401.12345") == "2401.12345"
        assert client._normalize_arxiv_id("ARXIV:2401.12345v1") == "2401.12345v1"
        assert client._normalize_arxiv_id("  arXiv:cs.AI/0123456  ") == "cs.AI/0123456"

    def test_crossref_client_normalize_doi(self) -> None:
        """Test CrossRefClient normalizes DOIs correctly."""
        client = CrossRefClient()

        # Valid DOI formats
        assert client._normalize_doi("10.1234/example") == "10.1234/example"
        assert client._normalize_doi("doi:10.1234/example") == "10.1234/example"
        assert client._normalize_doi("DOI:10.1234/example") == "10.1234/example"
        assert (
            client._normalize_doi("https://doi.org/10.1234/example")
            == "10.1234/example"
        )
        assert (
            client._normalize_doi("https://dx.doi.org/10.1234/example")
            == "10.1234/example"
        )

        # Invalid DOI formats should return None
        assert client._normalize_doi("invalid") is None
        assert client._normalize_doi("10.1234") is None  # No slash
        assert (
            client._normalize_doi("not.a.doi/example") is None
        )  # Doesn't start with 10.
        assert client._normalize_doi("") is None

    @patch("arxiv.Client")
    def test_arxiv_client_get_metadata_success(
        self, mock_arxiv_client_class: MagicMock
    ) -> None:
        """Test successful arXiv metadata retrieval."""
        client = ArxivClient()

        # Mock arxiv library and response
        mock_client = MagicMock()
        mock_arxiv_client_class.return_value = mock_client

        # Mock paper result
        mock_paper = MagicMock()
        mock_paper.title = "Test Paper Title"

        # Mock authors correctly - they have a .name attribute
        mock_author1 = MagicMock()
        mock_author1.name = "John Doe"
        mock_author2 = MagicMock()
        mock_author2.name = "Jane Smith"
        mock_paper.authors = [mock_author1, mock_author2]

        mock_paper.published = MagicMock(year=2024)
        mock_paper.summary = "This is a test abstract."
        mock_paper.entry_id = "http://arxiv.org/abs/2401.12345"
        mock_paper.categories = ["cs.AI", "cs.LG"]

        mock_client.results.return_value = [mock_paper]

        # Test metadata extraction
        result = client.get_metadata("2401.12345")

        assert result is not None
        assert result["title"] == "Test Paper Title"
        assert result["authors"] == ["John Doe", "Jane Smith"]
        assert result["year"] == 2024
        assert result["abstract"] == "This is a test abstract."
        assert result["arxiv_id"] == "2401.12345"
        assert result["url"] == "http://arxiv.org/abs/2401.12345"
        assert result["categories"] == ["cs.AI", "cs.LG"]

    @patch("arxiv.Client")
    def test_arxiv_client_get_metadata_not_found(
        self, mock_arxiv_client_class: MagicMock
    ) -> None:
        """Test arXiv metadata retrieval when paper not found."""
        client = ArxivClient()

        # Mock arxiv library - empty results
        mock_client = MagicMock()
        mock_arxiv_client_class.return_value = mock_client
        mock_client.results.return_value = []

        # Should return None for not found
        result = client.get_metadata("9999.99999")
        assert result is None

    def test_arxiv_client_get_metadata_no_arxiv_library(self) -> None:
        """Test ArxivClient graceful handling when arxiv library unavailable."""
        client = ArxivClient()

        # Mock import to fail
        with patch.dict("sys.modules", {"arxiv": None}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'arxiv'"),
            ):
                result = client.get_metadata("2401.12345")
                assert result is None

    @patch("requests.get")
    def test_crossref_client_get_metadata_success(self, mock_get: MagicMock) -> None:
        """Test successful CrossRef metadata retrieval."""
        client = CrossRefClient()

        # Mock successful CrossRef API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "title": ["Test Journal Article"],
                "author": [
                    {"given": "John", "family": "Doe"},
                    {"family": "Smith"},  # Only family name
                ],
                "published-print": {"date-parts": [[2023, 5, 15]]},
                "container-title": ["Nature"],
            }
        }
        mock_get.return_value = mock_response

        result = client.get_metadata("10.1234/example")

        assert result is not None
        assert result["title"] == "Test Journal Article"
        assert result["authors"] == ["John Doe", "Smith"]
        assert result["year"] == 2023
        assert result["doi"] == "10.1234/example"
        assert result["journal"] == "Nature"
        assert result["url"] == "https://doi.org/10.1234/example"

    @patch("requests.get")
    def test_crossref_client_get_metadata_not_found(self, mock_get: MagicMock) -> None:
        """Test CrossRef metadata retrieval when DOI not found."""
        client = CrossRefClient()

        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = client.get_metadata("10.9999/notfound")
        assert result is None

    @patch("requests.get")
    def test_crossref_client_handles_api_errors(self, mock_get: MagicMock) -> None:
        """Test CrossRef client handles API errors gracefully."""
        client = CrossRefClient()

        # Mock server error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = client.get_metadata("10.1234/example")
        assert result is None

    def test_crossref_client_extract_year_fallbacks(self) -> None:
        """Test CrossRef year extraction tries multiple date fields."""
        client = CrossRefClient()

        # Test published-print priority
        work1 = {"published-print": {"date-parts": [[2023]]}}
        assert client._extract_year(work1) == 2023

        # Test published-online fallback
        work2 = {"published-online": {"date-parts": [[2022]]}}
        assert client._extract_year(work2) == 2022

        # Test created fallback
        work3 = {"created": {"date-parts": [[2021]]}}
        assert client._extract_year(work3) == 2021

        # Test invalid year rejection
        work4 = {"published-print": {"date-parts": [[1700]]}}  # Too old
        assert client._extract_year(work4) is None


class TestEnhancedMetadataExtractor:
    """Test the complete metadata extraction orchestrator."""

    def test_extractor_initialization(self) -> None:
        """Test EnhancedMetadataExtractor can be initialized."""
        extractor = EnhancedMetadataExtractor()
        assert extractor is not None
        assert extractor.arxiv_client is not None
        assert extractor.crossref_client is not None
        assert len(extractor.text_extractors) == 2

    @patch("paperorganize.metadata_extraction.metadata_enricher.find_doi_patterns")
    @patch("paperorganize.metadata_extraction.metadata_enricher.find_arxiv_patterns")
    def test_extract_identifiers_and_enrich_with_text_extraction_failure(
        self, mock_find_arxiv: MagicMock, mock_find_doi: MagicMock
    ) -> None:
        """Test extraction when text extraction fails."""
        extractor = EnhancedMetadataExtractor()

        # Mock all text extractors to fail using patch.object
        with patch.object(
            extractor.text_extractors[0],
            "extract_text",
            side_effect=Exception("Extraction failed"),
        ):
            with patch.object(
                extractor.text_extractors[1],
                "extract_text",
                side_effect=Exception("Extraction failed"),
            ):
                metadata = PaperMetadata()

                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
                    extractor.extract_identifiers_and_enrich(tmp_file.name, metadata)

                # Should not call pattern matchers if no text extracted
                mock_find_doi.assert_not_called()
                mock_find_arxiv.assert_not_called()

    def test_extract_text_with_fallback_success(self) -> None:
        """Test text extraction fallback chain success."""
        extractor = EnhancedMetadataExtractor()

        # Mock first extractor to fail, second to succeed
        with patch.object(
            extractor.text_extractors[0],
            "extract_text",
            side_effect=Exception("First failed"),
        ):
            with patch.object(
                extractor.text_extractors[1],
                "extract_text",
                return_value="Extracted text",
            ):
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
                    result = extractor._extract_text_with_fallback(tmp_file.name)

                assert result == "Extracted text"

    def test_extract_text_with_fallback_all_fail(self) -> None:
        """Test text extraction when all extractors fail."""
        extractor = EnhancedMetadataExtractor()

        # Mock all extractors to fail
        with patch.object(
            extractor.text_extractors[0],
            "extract_text",
            side_effect=Exception("Failed"),
        ):
            with patch.object(
                extractor.text_extractors[1],
                "extract_text",
                side_effect=Exception("Failed"),
            ):
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
                    result = extractor._extract_text_with_fallback(tmp_file.name)

                assert result == ""

    def test_process_doi_matches_sets_doi(self) -> None:
        """Test DOI processing sets metadata.doi."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata()

        doi_match = IdentifierMatch(
            identifier="10.1234/example", identifier_type="doi", confidence=1.0
        )

        extractor._process_doi_matches([doi_match], metadata)

        assert metadata.doi == "10.1234/example"

    def test_process_arxiv_matches_sets_arxiv_id(self) -> None:
        """Test arXiv processing sets metadata.arxiv_id."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata()

        arxiv_match = IdentifierMatch(
            identifier="2401.12345", identifier_type="arxiv", confidence=1.0
        )

        extractor._process_arxiv_matches([arxiv_match], metadata)

        assert metadata.arxiv_id == "2401.12345"

    def test_process_matches_preserves_existing_identifiers(self) -> None:
        """Test that existing identifiers are not overwritten."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata(doi="existing.doi", arxiv_id="existing.arxiv")

        doi_match = IdentifierMatch("10.1234/new", "doi", 1.0)
        arxiv_match = IdentifierMatch("2401.99999", "arxiv", 1.0)

        extractor._process_doi_matches([doi_match], metadata)
        extractor._process_arxiv_matches([arxiv_match], metadata)

        # Should preserve existing values
        assert metadata.doi == "existing.doi"
        assert metadata.arxiv_id == "existing.arxiv"

    def test_merge_arxiv_metadata_updates_empty_fields(self) -> None:
        """Test arXiv metadata merging updates only empty fields."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata()  # Empty metadata

        arxiv_data = {
            "title": "arXiv Paper Title",
            "authors": ["Alice Author", "Bob Author"],
            "year": 2024,
            "abstract": "This is an arXiv abstract.",
        }

        extractor._merge_arxiv_metadata(arxiv_data, metadata)

        assert metadata.title == "arXiv Paper Title"
        assert metadata.authors == ["Alice Author", "Bob Author"]
        assert metadata.year == 2024

    def test_merge_arxiv_metadata_preserves_existing_data(self) -> None:
        """Test arXiv metadata merging preserves existing data."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata(
            title="Existing Title", authors=["Existing Author"], year=2023
        )

        arxiv_data = {
            "title": "arXiv Paper Title",
            "authors": ["Alice Author", "Bob Author"],
            "year": 2024,
        }

        extractor._merge_arxiv_metadata(arxiv_data, metadata)

        # Should preserve existing values
        assert metadata.title == "Existing Title"
        assert metadata.authors == ["Existing Author"]
        assert metadata.year == 2023

    def test_merge_crossref_metadata_updates_empty_fields(self) -> None:
        """Test CrossRef metadata merging updates only empty fields."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata()  # Empty metadata

        crossref_data = {
            "title": "Journal Article Title",
            "authors": ["John Researcher", "Jane Scientist"],
            "year": 2023,
            "journal": "Nature",
        }

        extractor._merge_crossref_metadata(crossref_data, metadata)

        assert metadata.title == "Journal Article Title"
        assert metadata.authors == ["John Researcher", "Jane Scientist"]
        assert metadata.year == 2023

    def test_merge_crossref_metadata_preserves_existing_data(self) -> None:
        """Test CrossRef metadata merging preserves existing data."""
        extractor = EnhancedMetadataExtractor()
        metadata = PaperMetadata(
            title="Existing Title", authors=["Existing Author"], year=2022
        )

        crossref_data = {
            "title": "Journal Article Title",
            "authors": ["John Researcher", "Jane Scientist"],
            "year": 2023,
        }

        extractor._merge_crossref_metadata(crossref_data, metadata)

        # Should preserve existing values
        assert metadata.title == "Existing Title"
        assert metadata.authors == ["Existing Author"]
        assert metadata.year == 2022


def test_integration_extract_pdf_metadata_with_enhanced_pipeline() -> None:
    """Integration test: extract_pdf_metadata uses enhanced pipeline instead of pdf2doi."""
    import tempfile
    from pathlib import Path
    from unittest.mock import patch, MagicMock
    from paperorganize.metadata import extract_pdf_metadata, PaperMetadata
    from paperorganize.metadata_extraction.metadata_enricher import (
        EnhancedMetadataExtractor,
    )

    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        # Mock the enhanced extraction availability and the extractor class
        with patch("paperorganize.metadata.ENHANCED_EXTRACTION_AVAILABLE", True):
            with patch(
                "paperorganize.metadata.EnhancedMetadataExtractor"
            ) as mock_extractor_class:
                mock_extractor = MagicMock(spec=EnhancedMetadataExtractor)
                mock_extractor_class.return_value = mock_extractor

                # Mock extract_identifiers_and_enrich to simulate finding DOI and enriching
                def mock_enrich(pdf_path: str, metadata: PaperMetadata) -> None:
                    # Simulate finding DOI and enriching from CrossRef
                    metadata.doi = "10.1234/example.doi"
                    metadata.title = "Example Paper Title from CrossRef"
                    metadata.authors = ["Dr. Jane Smith", "Prof. Bob Wilson"]
                    metadata.year = 2024

                mock_extractor.extract_identifiers_and_enrich.side_effect = mock_enrich

                # Also mock pypdf to avoid file access issues
                with patch("paperorganize.metadata.PDF_READER_AVAILABLE", False):
                    # Run the integration
                    result = extract_pdf_metadata(tmp_path)

                    # Verify enhanced extractor was called
                    mock_extractor_class.assert_called_once()
                    mock_extractor.extract_identifiers_and_enrich.assert_called_once_with(
                        tmp_path, result
                    )

                    # Verify metadata was enriched by enhanced pipeline
                    assert result.doi == "10.1234/example.doi"
                    assert result.title == "Example Paper Title from CrossRef"
                    assert result.authors == ["Dr. Jane Smith", "Prof. Bob Wilson"]
                    assert result.year == 2024

    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


def test_integration_enhanced_pipeline_preserves_pypdf_data() -> None:
    """Test enhanced pipeline preserves existing pypdf metadata."""
    import tempfile
    from pathlib import Path
    from unittest.mock import patch, MagicMock
    from paperorganize.metadata import extract_pdf_metadata, PaperMetadata
    from paperorganize.metadata_extraction.metadata_enricher import (
        EnhancedMetadataExtractor,
    )

    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        # Mock pypdf to return some basic metadata
        mock_reader = MagicMock()
        mock_reader.metadata = {
            "/Title": "Original PyPDF Title",
            "/Author": "Original Author",
        }

        with patch("paperorganize.metadata.ENHANCED_EXTRACTION_AVAILABLE", True):
            with patch("paperorganize.metadata.PdfReader", return_value=mock_reader):
                with patch("paperorganize.metadata.PDF_READER_AVAILABLE", True):
                    with patch(
                        "paperorganize.metadata.EnhancedMetadataExtractor"
                    ) as mock_extractor_class:
                        mock_extractor = MagicMock(spec=EnhancedMetadataExtractor)
                        mock_extractor_class.return_value = mock_extractor

                        # Mock enhanced extractor to only add DOI (preserving pypdf data)
                        def mock_enrich(pdf_path: str, metadata: PaperMetadata) -> None:
                            # Only add DOI, preserve existing title/authors from pypdf
                            metadata.doi = "10.1234/found.doi"
                            # Don't overwrite existing title/authors

                        mock_extractor.extract_identifiers_and_enrich.side_effect = (
                            mock_enrich
                        )

                        # Run the integration
                        result = extract_pdf_metadata(tmp_path)

                        # Verify pypdf data is preserved and enhanced data is added
                        assert result.title == "Original PyPDF Title"  # From pypdf
                        assert result.authors == ["Original Author"]  # From pypdf
                        assert (
                            result.doi == "10.1234/found.doi"
                        )  # From enhanced pipeline

    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
