# ABOUTME: Public interfaces for metadata extraction module
# ABOUTME: Provides Protocol definitions and main extraction function
# SPDX-License-Identifier: MIT

"""Enhanced metadata extraction with MIT-licensed components.

This module replaces AGPL-licensed pdf2doi with a combination of MIT-licensed tools:
- pdfplumber for enhanced PDF text extraction
- arxiv.py for direct arXiv API access
- CrossRef REST API for DOI validation and metadata enrichment

Public Interface:
    extract_enhanced_metadata: Main extraction function compatible with existing code
    PaperMetadata: Shared metadata structure (re-exported from metadata.py)
"""

from paperorganize.models import PaperMetadata

__all__ = ["PaperMetadata"]
