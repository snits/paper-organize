# ABOUTME: Tests for enhanced metadata extraction components
# ABOUTME: Covers text extractors, pattern matchers, and orchestration layer
# SPDX-License-Identifier: MIT

import tempfile
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
    """Test API client interfaces."""

    def test_arxiv_client_initialization(self) -> None:
        """Test ArxivClient can be initialized."""
        client = ArxivClient()
        assert client is not None

    def test_crossref_client_initialization(self) -> None:
        """Test CrossRefClient can be initialized."""
        client = CrossRefClient()
        assert client is not None

    def test_arxiv_client_get_metadata_placeholder(self) -> None:
        """Test ArxivClient.get_metadata returns None (placeholder implementation)."""
        client = ArxivClient()
        result = client.get_metadata("2401.12345")
        assert result is None

    def test_crossref_client_get_metadata_placeholder(self) -> None:
        """Test CrossRefClient.get_metadata returns None (placeholder implementation)."""
        client = CrossRefClient()
        result = client.get_metadata("10.1234/example")
        assert result is None


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
