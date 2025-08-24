# ABOUTME: arXiv and CrossRef API clients with caching and rate limiting
# ABOUTME: MIT-licensed API integrations for metadata enrichment
# SPDX-License-Identifier: MIT

"""API clients for academic metadata enrichment.

Provides MIT-licensed API clients for:
- arXiv API using official arxiv.py library
- CrossRef REST API for DOI validation and metadata
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

# HTTP status codes
HTTP_OK = 200
HTTP_NOT_FOUND = 404

# Academic year validation constants
MIN_ACADEMIC_YEAR = 1800
MAX_ACADEMIC_YEAR = 2100

logger = logging.getLogger(__name__)


class ArxivClient:
    """Official arXiv API client with caching and error handling."""

    def __init__(self) -> None:
        """Initialize arXiv client with rate limiting."""
        self._last_request_time = 0.0
        self._min_request_interval = 3.0  # Polite rate limiting for arXiv API

    def get_metadata(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for arXiv paper using official arxiv.py library.

        Args:
            arxiv_id: arXiv identifier (e.g., "2401.12345" or "cs.AI/0123456")

        Returns:
            Optional[Dict[str, Any]]: Metadata dict with title, authors, year, etc.
                                    None if not found or error occurred
        """
        try:
            import arxiv  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("arxiv library not available, cannot fetch arXiv metadata")
            return None

        # Rate limiting - be polite to arXiv API
        self._apply_rate_limit()

        try:
            # Clean up arXiv ID format
            clean_id = self._normalize_arxiv_id(arxiv_id)
            logger.debug("Fetching arXiv metadata for ID: %s", clean_id)

            # Search for the paper
            client = arxiv.Client()
            search = arxiv.Search(id_list=[clean_id], max_results=1)
            results = list(client.results(search))

            if not results:
                logger.debug("No arXiv paper found for ID: %s", clean_id)
                return None

            paper = results[0]

            # Extract metadata in our standard format
            metadata = {
                "title": paper.title.strip() if paper.title else None,
                "authors": [author.name for author in paper.authors]
                if paper.authors
                else [],
                "year": paper.published.year if paper.published else None,
                "abstract": paper.summary.strip() if paper.summary else None,
                "arxiv_id": clean_id,
                "url": paper.entry_id,
                "categories": paper.categories if paper.categories else [],
            }

            logger.debug("Successfully retrieved arXiv metadata for %s", clean_id)
            return metadata

        except Exception as e:
            logger.warning("Failed to fetch arXiv metadata for %s: %s", arxiv_id, e)
            return None

    def _apply_rate_limit(self) -> None:
        """Apply polite rate limiting for arXiv API."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug("Rate limiting: sleeping %.2f seconds", sleep_time)
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _normalize_arxiv_id(self, arxiv_id: str) -> str:
        """Normalize arXiv ID to standard format.

        Args:
            arxiv_id: Raw arXiv ID that may include prefix or version

        Returns:
            str: Normalized arXiv ID
        """
        # Remove common prefixes
        clean_id = arxiv_id.strip()
        clean_id = re.sub(r"^arXiv:", "", clean_id, flags=re.IGNORECASE)
        return clean_id.strip()

        # arXiv API expects ID without version for search, but we keep version for accuracy


class CrossRefClient:
    """CrossRef REST API client with rate limiting and caching."""

    def __init__(self) -> None:
        """Initialize CrossRef client with rate limiting."""
        self._last_request_time = 0.0
        self._min_request_interval = 1.0  # CrossRef allows higher rates than arXiv
        self._base_url = "https://api.crossref.org/works/"
        self._headers = {
            "User-Agent": "paper-organize/1.0.0 (https://github.com/your-repo; mailto:your-email@domain.com)",
            "Accept": "application/json",
        }

    def get_metadata(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get metadata for DOI using CrossRef REST API.

        Args:
            doi: DOI identifier (e.g., "10.1234/example.doi")

        Returns:
            Optional[Dict[str, Any]]: Metadata dict with title, authors, year, etc.
                                    None if not found or error occurred
        """
        # Rate limiting - be polite to CrossRef API
        self._apply_rate_limit()

        try:
            import requests
        except ImportError:
            logger.warning(
                "requests library not available, cannot fetch CrossRef metadata"
            )
            return None

        try:
            # Clean and validate DOI
            clean_doi = self._normalize_doi(doi)
            if not clean_doi:
                logger.debug("Invalid DOI format: %s", doi)
                return None

            url = f"{self._base_url}{clean_doi}"
            logger.debug("Fetching CrossRef metadata for DOI: %s", clean_doi)

            # Make request to CrossRef API
            response = requests.get(url, headers=self._headers, timeout=10)

            if response.status_code == HTTP_NOT_FOUND:
                logger.debug("DOI not found in CrossRef: %s", clean_doi)
                return None
            if response.status_code != HTTP_OK:
                logger.warning(
                    "CrossRef API error for %s: HTTP %d",
                    clean_doi,
                    response.status_code,
                )
                return None

            data = response.json()
            work = data.get("message", {})

            # Extract metadata in our standard format
            metadata = {
                "title": self._extract_title(work),
                "authors": self._extract_authors(work),
                "year": self._extract_year(work),
                "doi": clean_doi,
                "journal": self._extract_journal(work),
                "url": f"https://doi.org/{clean_doi}",
            }

            logger.debug("Successfully retrieved CrossRef metadata for %s", clean_doi)
            return metadata

        except Exception as e:
            logger.warning("Failed to fetch CrossRef metadata for %s: %s", doi, e)
            return None

    def _apply_rate_limit(self) -> None:
        """Apply polite rate limiting for CrossRef API."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug("Rate limiting: sleeping %.2f seconds", sleep_time)
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _normalize_doi(self, doi: str) -> Optional[str]:
        """Normalize DOI to standard format and validate.

        Args:
            doi: Raw DOI that may include URL or prefix

        Returns:
            Optional[str]: Normalized DOI or None if invalid
        """
        if not doi:
            return None

        # Remove common prefixes and clean up
        clean_doi = doi.strip()
        clean_doi = re.sub(
            r"^https?://(?:dx\.)?doi\.org/", "", clean_doi, flags=re.IGNORECASE
        )
        clean_doi = re.sub(r"^doi:", "", clean_doi, flags=re.IGNORECASE).strip()

        # Validate DOI format (must start with 10. and contain /)
        if not clean_doi.startswith("10.") or "/" not in clean_doi:
            return None

        return clean_doi

    def _extract_title(self, work: Dict[str, Any]) -> Optional[str]:
        """Extract title from CrossRef work data."""
        titles = work.get("title", [])
        if titles and isinstance(titles, list):
            return titles[0].strip() if titles[0] else None
        return None

    def _extract_authors(self, work: Dict[str, Any]) -> List[str]:
        """Extract authors from CrossRef work data."""
        authors = []
        for author in work.get("author", []):
            if isinstance(author, dict):
                given = author.get("given", "").strip()
                family = author.get("family", "").strip()

                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)

        return authors

    def _extract_year(self, work: Dict[str, Any]) -> Optional[int]:
        """Extract publication year from CrossRef work data."""
        # Try different date fields
        for date_field in ["published-print", "published-online", "created"]:
            date_parts = work.get(date_field, {}).get("date-parts", [])
            if date_parts and len(date_parts[0]) > 0:
                try:
                    year = int(date_parts[0][0])
                    if MIN_ACADEMIC_YEAR <= year <= MAX_ACADEMIC_YEAR:  # Reasonable year range
                        return year
                except (ValueError, TypeError, IndexError):
                    continue
        return None

    def _extract_journal(self, work: Dict[str, Any]) -> Optional[str]:
        """Extract journal name from CrossRef work data."""
        containers = work.get("container-title", [])
        if containers and isinstance(containers, list):
            return containers[0].strip() if containers[0] else None
        return None
