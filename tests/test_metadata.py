# ABOUTME: Metadata extraction tests for PDF parsing and filename generation
# ABOUTME: Tests title/author extraction and filesystem-safe name creation

import pytest

from paperdl.metadata import extract_metadata, generate_filename


def test_extract_metadata_not_implemented():
    """Test extract_metadata raises NotImplementedError until implemented."""
    with pytest.raises(NotImplementedError):
        extract_metadata("/tmp/test.pdf")


def test_generate_filename_not_implemented():
    """Test generate_filename raises NotImplementedError until implemented."""
    metadata = {"title": "Test Paper", "authors": ["Test Author"], "year": 2023}
    with pytest.raises(NotImplementedError):
        generate_filename(metadata, "original.pdf")
