# ABOUTME: DOI and arXiv pattern matching with confidence scoring
# ABOUTME: Comprehensive regex patterns for academic identifier extraction
# SPDX-License-Identifier: MIT

"""Pattern matching for academic identifiers in PDF text.

Provides robust pattern matching for:
- DOI patterns with various formats and prefixes
- arXiv identifiers in both old and new formats
- Confidence scoring for pattern matches
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class IdentifierMatch:
    """Represents a matched academic identifier with confidence."""

    identifier: str
    identifier_type: str  # "doi" | "arxiv"
    confidence: float  # 0.0 - 1.0


# DOI pattern matching
DOI_PATTERNS = [
    # Standard DOI format: 10.xxxx/xxxxx
    (r"\b10\.\d{4,}\/[^\s\]]+", 1.0),
    # DOI with prefix: "doi: 10.xxxx/xxxxx" or "DOI: 10.xxxx/xxxxx"
    (r"(?i)\bdoi\s*[:=]\s*(10\.\d{4,}\/[^\s\]]+)", 0.95),
    # DOI URL format: https://doi.org/10.xxxx/xxxxx
    (r"https?://(?:dx\.)?doi\.org/(10\.\d{4,}\/[^\s\]]+)", 0.9),
    # DOI in brackets or parentheses
    (r"[\[\(]doi\s*[:=]?\s*(10\.\d{4,}\/[^\s\]\)]+)[\]\)]", 0.8),
]

# arXiv pattern matching
ARXIV_PATTERNS = [
    # New arXiv format: YYMM.NNNNN[vN] (since 2007)
    (r"\b(?:arXiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)\b", 1.0),
    # arXiv with explicit prefix
    (r"(?i)\barxiv\s*[:=]\s*(\d{4}\.\d{4,5}(?:v\d+)?)", 0.95),
    # arXiv URL format: https://arxiv.org/abs/YYMM.NNNNN
    (r"https?://arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", 0.9),
    # Old arXiv format: subject-class/YYMMnnn (pre-2007)
    (r"\b(?:arXiv:)?([a-z-]+(?:\.[A-Z]{2})?/\d{7})\b", 0.8),
    # Old arXiv with URL
    (r"https?://arxiv\.org/(?:abs|pdf)/([a-z-]+(?:\.[A-Z]{2})?/\d{7})", 0.75),
]


def find_doi_patterns(text: str) -> List[IdentifierMatch]:
    """Find DOI patterns in text with confidence scoring.

    Args:
        text: Text to search for DOI patterns

    Returns:
        List[IdentifierMatch]: Found DOI matches sorted by confidence
    """
    matches = []

    for pattern, confidence in DOI_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Extract DOI - pattern may have capturing group
            if match.groups():
                doi = match.group(1).strip()
            else:
                doi = match.group(0).strip()

            # Clean up DOI - remove common trailing punctuation
            doi = re.sub(r"[.,;:\]]+$", "", doi)

            # Basic validation - DOI should have reasonable format
            if len(doi) > 7 and "/" in doi and doi.startswith("10."):
                matches.append(
                    IdentifierMatch(
                        identifier=doi, identifier_type="doi", confidence=confidence
                    )
                )
                logger.debug(
                    "Found DOI pattern '%s' with confidence %.2f", doi, confidence
                )

    # Remove duplicates and sort by confidence
    unique_matches: Dict[str, IdentifierMatch] = {}
    for identifier_match in matches:
        if (
            identifier_match.identifier not in unique_matches
            or identifier_match.confidence
            > unique_matches[identifier_match.identifier].confidence
        ):
            unique_matches[identifier_match.identifier] = identifier_match

    return sorted(unique_matches.values(), key=lambda x: x.confidence, reverse=True)


def find_arxiv_patterns(text: str) -> List[IdentifierMatch]:
    """Find arXiv ID patterns in text with confidence scoring.

    Args:
        text: Text to search for arXiv patterns

    Returns:
        List[IdentifierMatch]: Found arXiv matches sorted by confidence
    """
    matches = []

    for pattern, confidence in ARXIV_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Extract arXiv ID - pattern may have capturing group
            if match.groups():
                arxiv_id = match.group(1).strip()
            else:
                arxiv_id = match.group(0).strip()

            # Clean up arXiv ID
            arxiv_id = arxiv_id.replace("arXiv:", "").strip()

            # Basic validation for arXiv format
            if _is_valid_arxiv_format(arxiv_id):
                matches.append(
                    IdentifierMatch(
                        identifier=arxiv_id,
                        identifier_type="arxiv",
                        confidence=confidence,
                    )
                )
                logger.debug(
                    "Found arXiv pattern '%s' with confidence %.2f",
                    arxiv_id,
                    confidence,
                )

    # Remove duplicates and sort by confidence
    unique_matches: Dict[str, IdentifierMatch] = {}
    for identifier_match in matches:
        if (
            identifier_match.identifier not in unique_matches
            or identifier_match.confidence
            > unique_matches[identifier_match.identifier].confidence
        ):
            unique_matches[identifier_match.identifier] = identifier_match

    return sorted(unique_matches.values(), key=lambda x: x.confidence, reverse=True)


def _is_valid_arxiv_format(arxiv_id: str) -> bool:
    """Validate arXiv ID format.

    Args:
        arxiv_id: arXiv identifier to validate

    Returns:
        bool: True if format is valid
    """
    # New format: YYMM.NNNNN[vN]
    if re.match(r"^\d{4}\.\d{4,5}(?:v\d+)?$", arxiv_id):
        return True

    # Old format: subject-class/YYMMnnn
    if re.match(r"^[a-z-]+(?:\.[A-Z]{2})?/\d{7}$", arxiv_id):
        return True

    return False
