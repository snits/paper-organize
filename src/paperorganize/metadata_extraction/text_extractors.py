# ABOUTME: PDF text extraction strategies with fallback chain
# ABOUTME: Protocol-based design with pdfplumber and pypdf implementations
# SPDX-License-Identifier: MIT

"""PDF text extraction with enhanced layout handling.

Provides multiple text extraction strategies:
1. PdfPlumberExtractor - Enhanced extraction with layout preservation
2. PyPDFExtractor - Reliable fallback using existing pypdf dependency
"""

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class PDFTextExtractor(Protocol):
    """Protocol for PDF text extraction implementations."""

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text content

        Raises:
            Exception: Any extraction errors should be caught by caller
        """
        ...


class PdfPlumberExtractor:
    """Enhanced text extraction using pdfplumber with layout preservation."""

    def extract_text(self, pdf_path: str) -> str:
        """Extract text using pdfplumber with better layout handling.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text with preserved structure

        Raises:
            Exception: pdfplumber import or processing errors
        """
        try:
            import pdfplumber
        except ImportError as e:
            msg = "pdfplumber not available"
            raise ImportError(msg) from e

        text_parts = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Process first 5 pages only for performance
                max_pages = min(5, len(pdf.pages))

                for page_num in range(max_pages):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()

                    if page_text:
                        text_parts.append(page_text.strip())

                    # Early exit optimization - stop when we have enough text
                    # for pattern matching (typically first page has identifiers)
                    text_extraction_limit = (
                        5000  # Reasonable text limit for pattern matching
                    )
                    if len("".join(text_parts)) > text_extraction_limit:
                        break

        except Exception as e:
            logger.debug("pdfplumber extraction failed for %s: %s", pdf_path, e)
            raise

        return "\n".join(text_parts)


class PyPDFExtractor:
    """Fallback text extraction using existing pypdf dependency."""

    def extract_text(self, pdf_path: str) -> str:
        """Extract text using pypdf as reliable fallback.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text content

        Raises:
            Exception: pypdf import or processing errors
        """
        try:
            from pypdf import PdfReader
        except ImportError as e:
            msg = "pypdf library not available"
            raise ImportError(msg) from e

        text_parts = []

        try:
            reader = PdfReader(pdf_path)
            # Process first 5 pages only for performance
            max_pages = min(5, len(reader.pages))

            for page_num in range(max_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()

                if page_text:
                    text_parts.append(page_text.strip())

                # Early exit optimization
                text_extraction_limit = (
                    5000  # Reasonable text limit for pattern matching
                )
                if len("".join(text_parts)) > text_extraction_limit:
                    break

        except Exception as e:
            logger.debug("pypdf extraction failed for %s: %s", pdf_path, e)
            raise

        return "\n".join(text_parts)
