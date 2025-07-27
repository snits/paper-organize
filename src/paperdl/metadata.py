# ABOUTME: PDF metadata extraction and filename generation logic
# ABOUTME: Extracts titles/authors from PDFs and creates filesystem-safe names

import datetime
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, List, Optional

# Constants for academic year validation
MIN_ACADEMIC_YEAR = 1900
MAX_YEAR_OFFSET = 5

try:
    from pypdf import PdfReader
    PDF_READER_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader  # type: ignore[assignment]
        PDF_READER_AVAILABLE = True
    except ImportError:
        PDF_READER_AVAILABLE = False
        PdfReader = Any  # type: ignore[assignment,misc]

try:
    import pdf2doi  # type: ignore[import-untyped]
except ImportError:
    pdf2doi = None

logger = logging.getLogger(__name__)

def _is_valid_academic_year(year: int) -> bool:
    """Check if year is reasonable for academic papers."""
    current_year = datetime.datetime.now(tz=datetime.timezone.utc).year
    return MIN_ACADEMIC_YEAR <= year <= current_year + MAX_YEAR_OFFSET


@dataclass
class PaperMetadata:
    """Structured metadata for academic papers."""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    year: Optional[int] = None

    def __post_init__(self) -> None:
        """Initialize authors list if None."""
        if self.authors is None:
            self.authors = []


def extract_pdf_metadata(pdf_path: str) -> PaperMetadata:
    """Extract metadata from PDF using layered approach.

    Uses multiple extraction methods in order of reliability:
    1. pypdf for standard PDF metadata
    2. pdf2doi for academic identifiers (DOI, arXiv)
    3. Graceful fallback for missing/corrupted files

    Args:
        pdf_path: Path to PDF file

    Returns:
        PaperMetadata: Structured metadata object
    """
    metadata = PaperMetadata()

    # Layer 1: Try pypdf for basic metadata
    _extract_with_pypdf(pdf_path, metadata)

    # Layer 2: Try pdf2doi for academic identifiers
    _extract_with_pdf2doi(pdf_path, metadata)

    # Layer 3: Extract year from title if not found yet
    if not metadata.year and metadata.title:
        _extract_year_from_title(metadata.title, metadata)

    return metadata


def _extract_year_from_pdf_dates(pdf_meta: dict, metadata: PaperMetadata) -> None:
    """Extract year from PDF creation or modification dates."""
    for date_field in ["/CreationDate", "/ModDate"]:
        if pdf_meta.get(date_field) and not metadata.year:
            try:
                date_str = str(pdf_meta[date_field])
                # Extract year from date string (format: D:YYYYMMDDHHmmSSOHH'mm')
                year_match = re.search(r"D:(\d{4})", date_str)
                if year_match:
                    year = int(year_match.group(1))
                    if _is_valid_academic_year(year):
                        metadata.year = year
                        break
            except (ValueError, TypeError):
                continue


def _extract_year_from_title(title: str, metadata: PaperMetadata) -> None:
    """Extract year from paper title as fallback method."""
    # Look for 4-digit years in parentheses or brackets (common in academic titles)
    year_patterns = [
        r"\((\d{4})\)",  # (2024)
        r"\[(\d{4})\]",  # [2024]
        r"\b(\d{4})\b",  # standalone 4-digit number
    ]

    for pattern in year_patterns:
        matches = re.findall(pattern, title)
        if matches:
            # Take the last match (most likely to be publication year)
            try:
                year = int(matches[-1])
                # Sanity check: reasonable year range for academic papers
                if _is_valid_academic_year(year):
                    metadata.year = year
                    logger.debug("Extracted year %d from title: %s", year, title)
                    return
            except ValueError:
                continue


def _extract_with_pypdf(pdf_path: str, metadata: PaperMetadata) -> None:
    """Extract basic metadata using pypdf."""
    if not PDF_READER_AVAILABLE:
        return

    try:
        reader = PdfReader(pdf_path)
        if hasattr(reader, "metadata") and reader.metadata:
            pdf_meta = reader.metadata

            # Extract title
            if pdf_meta.get("/Title"):
                metadata.title = str(pdf_meta["/Title"]).strip()

            # Extract authors - handle various formats
            if pdf_meta.get("/Author"):
                author_str = str(pdf_meta["/Author"]).strip()
                # Split on common delimiters
                metadata.authors = [
                    author.strip()
                    for author in re.split(r"[,;]|\sand\s", author_str)
                    if author.strip()
                ]

            # Extract year from PDF dates
            if not metadata.year:
                _extract_year_from_pdf_dates(pdf_meta, metadata)

    except Exception as e:
        # Log error but continue gracefully if pypdf fails
        logger.debug("Failed to extract metadata with pypdf from %s: %s", pdf_path, e)


def _extract_with_pdf2doi(pdf_path: str, metadata: PaperMetadata) -> None:
    """Extract academic identifiers using pdf2doi."""
    if pdf2doi is None:
        return

    try:
        result = pdf2doi.pdf2doi(pdf_path)
        if result and isinstance(result, dict):
            identifier = result.get("identifier", "")
            identifier_type = result.get("identifier_type", "")

            if identifier_type == "doi":
                metadata.doi = identifier
            elif identifier_type == "arxiv":
                metadata.arxiv_id = identifier

    except Exception as e:
        # Log error but continue gracefully if pdf2doi fails
        logger.debug("Failed to extract identifiers with pdf2doi from %s: %s", pdf_path, e)


def generate_filename(metadata: PaperMetadata, fallback_name: str) -> str:
    """Generate clean filename from metadata.

    Creates filesystem-safe filenames in format:
    - With author + year: "LastName_YYYY_Title.pdf"
    - With year only: "YYYY_Title.pdf"
    - With title only: "Title.pdf"
    - No metadata: fallback to original filename

    Args:
        metadata: PaperMetadata object
        fallback_name: Original filename to use if metadata insufficient

    Returns:
        str: Filesystem-safe filename
    """
    # Check if we have sufficient metadata
    if not metadata.title:
        return fallback_name

    parts = []

    # Add first author's last name if available
    if metadata.authors:
        first_author = metadata.authors[0]
        # Extract last name (handle various formats)
        author_parts = first_author.strip().split()
        if author_parts:
            last_name = author_parts[-1]
            # Sanitize author name
            last_name = _sanitize_filename_part(last_name)
            if last_name:
                parts.append(last_name)

    # Add year if available
    if metadata.year:
        parts.append(str(metadata.year))

    # Add sanitized title
    title = _sanitize_filename_part(metadata.title)
    if title:
        parts.append(title)

    # Join parts with underscores
    if parts:
        filename = "_".join(parts)

        # Truncate if too long (keep reasonable filename length)
        max_length = 90  # Leave room for .pdf extension
        min_parts_for_truncation = 2
        if len(filename) > max_length:
            # Try to truncate title part while keeping author and year
            if len(parts) >= min_parts_for_truncation:
                prefix = "_".join(parts[:-1]) + "_"
                title_max = max_length - len(prefix)
                truncated_title = parts[-1][:title_max].rstrip("_")
                filename = prefix + truncated_title
            else:
                filename = filename[:max_length].rstrip("_")

        return filename + ".pdf"

    # Fallback to original if no usable metadata
    return fallback_name


def _sanitize_filename_part(text: str) -> str:
    """Sanitize text for filesystem-safe filename component.

    Args:
        text: Input text to sanitize

    Returns:
        str: Sanitized text safe for filenames
    """
    if not text:
        return ""

    # Normalize Unicode characters to ASCII equivalents
    # This handles accented characters properly (á->a, ñ->n, etc.)
    try:
        sanitized = unicodedata.normalize("NFKD", text)
        sanitized = sanitized.encode("ascii", "ignore").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        # Fallback to original text if Unicode normalization fails
        logger.debug("Unicode normalization failed for text: %s", text)
        sanitized = text

    # Replace filesystem-unsafe characters with underscores
    # Covers: / \ : * ? " < > | & ( ) [ ] { } . % $ # @ ! ^ ` ~ + = ; ' ,
    sanitized = re.sub(r'[/\\:*?"<>|&()\[\]{}\.%$#@!^`~+=;\',]', "_", sanitized)

    # Remove any remaining non-alphanumeric characters except hyphens and underscores
    sanitized = re.sub(r"[^\w\s_-]", "", sanitized)

    # Replace multiple whitespace with single underscore
    sanitized = re.sub(r"[\s]+", "_", sanitized)

    # Collapse multiple underscores into single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing underscores and validate length
    sanitized = sanitized.strip("_")

    # Ensure component isn't too long (filesystem limits)
    max_component_length = 50
    if len(sanitized) > max_component_length:
        # Truncate but try to preserve word boundaries
        truncated = sanitized[:max_component_length].rsplit("_", 1)[0]
        sanitized = truncated if truncated else sanitized[:max_component_length]
        logger.debug("Truncated filename component: %s -> %s", text, sanitized)

    return sanitized
