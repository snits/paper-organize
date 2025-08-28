# ABOUTME: Orchestrates the complete metadata extraction pipeline
# ABOUTME: Coordinates text extraction, pattern matching, and API enrichment
# SPDX-License-Identifier: MIT

"""Enhanced metadata extraction orchestration.

Coordinates the complete extraction pipeline:
1. Text extraction using fallback chain
2. Pattern matching with confidence scoring
3. API validation and metadata enrichment
4. Integration with existing PaperMetadata structure
"""

import logging
from typing import List

from paperorganize.models import PaperMetadata

from .api_clients import ArxivClient, CrossRefClient
from .pattern_matchers import IdentifierMatch, find_arxiv_patterns, find_doi_patterns
from .text_extractors import PdfPlumberExtractor, PDFTextExtractor, PyPDFExtractor

logger = logging.getLogger(__name__)


class EnhancedMetadataExtractor:
    """Orchestrates the complete extraction pipeline."""

    def __init__(self) -> None:
        """Initialize extractor with API clients and text extractors."""
        self.arxiv_client = ArxivClient()
        self.crossref_client = CrossRefClient()

        # Text extractors in fallback order (best to most reliable)
        self.text_extractors: List[PDFTextExtractor] = [
            PdfPlumberExtractor(),
            PyPDFExtractor(),
        ]

    def extract_identifiers_and_enrich(
        self, pdf_path: str, metadata: PaperMetadata
    ) -> None:
        """Extract identifiers from PDF and enrich metadata via APIs.

        Args:
            pdf_path: Path to PDF file
            metadata: PaperMetadata object to enrich (modified in place)
        """
        # Step 1: Extract text using fallback chain
        text = self._extract_text_with_fallback(pdf_path)
        if not text:
            logger.debug("No text extracted from %s", pdf_path)
            return

        # Step 2: Find patterns with confidence scoring
        doi_matches = find_doi_patterns(text)
        arxiv_matches = find_arxiv_patterns(text)

        # Step 3: Validate and enrich via appropriate APIs
        self._process_doi_matches(doi_matches, metadata)
        self._process_arxiv_matches(arxiv_matches, metadata)

        logger.debug("Enhanced extraction completed for %s", pdf_path)

    def _extract_text_with_fallback(self, pdf_path: str) -> str:
        """Extract text using extractor fallback chain.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text or empty string if all extractors fail
        """
        for extractor in self.text_extractors:
            try:
                text = extractor.extract_text(pdf_path)
                if text.strip():
                    extractor_name = extractor.__class__.__name__
                    logger.debug("Successfully extracted text using %s", extractor_name)
                    return text
            except Exception as e:
                extractor_name = extractor.__class__.__name__
                logger.debug("Text extraction failed with %s: %s", extractor_name, e)
                continue

        logger.warning("All text extractors failed for %s", pdf_path)
        return ""

    def _process_doi_matches(
        self, doi_matches: List[IdentifierMatch], metadata: PaperMetadata
    ) -> None:
        """Process DOI matches and enrich metadata.

        Args:
            doi_matches: List of DOI matches sorted by confidence
            metadata: PaperMetadata to enrich
        """
        if not doi_matches:
            return

        # Take highest confidence match
        best_match = doi_matches[0]
        logger.debug(
            "Processing DOI match: %s (confidence: %.2f)",
            best_match.identifier,
            best_match.confidence,
        )

        # Set DOI if not already present
        if not metadata.doi:
            metadata.doi = best_match.identifier

        # Enrich with CrossRef metadata (implementation in later commits)
        crossref_metadata = self.crossref_client.get_metadata(best_match.identifier)
        if crossref_metadata:
            self._merge_crossref_metadata(crossref_metadata, metadata)

    def _process_arxiv_matches(
        self, arxiv_matches: List[IdentifierMatch], metadata: PaperMetadata
    ) -> None:
        """Process arXiv matches and enrich metadata.

        Args:
            arxiv_matches: List of arXiv matches sorted by confidence
            metadata: PaperMetadata to enrich
        """
        if not arxiv_matches:
            return

        # Take highest confidence match
        best_match = arxiv_matches[0]
        logger.debug(
            "Processing arXiv match: %s (confidence: %.2f)",
            best_match.identifier,
            best_match.confidence,
        )

        # Set arXiv ID if not already present
        if not metadata.arxiv_id:
            metadata.arxiv_id = best_match.identifier

        # Enrich with arXiv metadata (implementation in later commits)
        arxiv_metadata = self.arxiv_client.get_metadata(best_match.identifier)
        if arxiv_metadata:
            self._merge_arxiv_metadata(arxiv_metadata, metadata)

    def _merge_crossref_metadata(
        self, crossref_data: dict, metadata: PaperMetadata
    ) -> None:
        """Merge CrossRef metadata into PaperMetadata.

        Args:
            crossref_data: CrossRef API response data
            metadata: PaperMetadata to update
        """
        # Only update fields that are currently empty to avoid overwriting pypdf data
        if not metadata.title and crossref_data.get("title"):
            metadata.title = crossref_data["title"]
            logger.debug("Updated title from CrossRef: %s", metadata.title)

        if not metadata.authors and crossref_data.get("authors"):
            metadata.authors = crossref_data["authors"]
            logger.debug("Updated authors from CrossRef: %s", metadata.authors)

        if not metadata.year and crossref_data.get("year"):
            metadata.year = crossref_data["year"]
            logger.debug("Updated year from CrossRef: %s", metadata.year)

    def _merge_arxiv_metadata(self, arxiv_data: dict, metadata: PaperMetadata) -> None:
        """Merge arXiv metadata into PaperMetadata.

        Args:
            arxiv_data: arXiv API response data
            metadata: PaperMetadata to update
        """
        # Only update fields that are currently empty to avoid overwriting pypdf data
        if not metadata.title and arxiv_data.get("title"):
            metadata.title = arxiv_data["title"]
            logger.debug("Updated title from arXiv: %s", metadata.title)

        if not metadata.authors and arxiv_data.get("authors"):
            metadata.authors = arxiv_data["authors"]
            logger.debug("Updated authors from arXiv: %s", metadata.authors)

        if not metadata.year and arxiv_data.get("year"):
            metadata.year = arxiv_data["year"]
            logger.debug("Updated year from arXiv: %s", metadata.year)
