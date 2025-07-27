# ABOUTME: PDF metadata extraction and filename generation logic
# ABOUTME: Extracts titles/authors from PDFs and creates filesystem-safe names

import re
from dataclasses import dataclass
from typing import Any, List, Optional

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

    return metadata


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

    except Exception:
        # Continue gracefully if pypdf fails
        pass


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

    except Exception:
        # Continue gracefully if pdf2doi fails
        pass


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

    # Handle accented characters first (basic approach)
    sanitized = text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    sanitized = sanitized.replace("ñ", "n").replace("ç", "c")
    sanitized = sanitized.replace("à", "a").replace("è", "e").replace("ì", "i").replace("ò", "o").replace("ù", "u")

    # Replace problematic characters with underscores or remove them
    sanitized = re.sub(r'[&/\\:*?"<>|]', "_", sanitized)  # Replace filesystem-unsafe chars with underscore
    sanitized = re.sub(r"[^\w\s_-]", "", sanitized)  # Remove remaining special chars, keep word chars, spaces, underscores, hyphens
    sanitized = re.sub(r"[\s]+", "_", sanitized)  # Replace spaces with underscores
    sanitized = re.sub(r"_+", "_", sanitized)  # Collapse multiple underscores

    # Remove leading/trailing underscores
    return sanitized.strip("_")
