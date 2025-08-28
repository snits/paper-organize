# ABOUTME: Shared data models for academic paper metadata
# ABOUTME: Defines PaperMetadata structure used throughout the application
# SPDX-License-Identifier: MIT

"""Shared data models for academic paper metadata.

This module defines the core data structures used throughout the paper organization
system to avoid circular import dependencies.
"""

from dataclasses import dataclass
from typing import List, Optional


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
