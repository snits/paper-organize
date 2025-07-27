# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

from paperorganize.exceptions import ValidationError
from paperorganize.input_detection import (
    InputType,
    detect_input_type,
    validate_directory_contains_pdfs,
)


class TestDetectInputType:
    """Test input type detection functionality."""

    def test_detect_url_http(self) -> None:
        """Test detection of HTTP URLs."""
        result = detect_input_type("http://example.com/paper.pdf")
        assert result == InputType.URL

    def test_detect_url_https(self) -> None:
        """Test detection of HTTPS URLs."""
        result = detect_input_type("https://arxiv.org/pdf/2301.00001.pdf")
        assert result == InputType.URL

    def test_detect_invalid_url(self) -> None:
        """Test rejection of invalid URLs."""
        with pytest.raises(ValidationError) as exc_info:
            detect_input_type("http://")

        assert "Invalid URL" in str(exc_info.value)

    def test_detect_file(self, tmp_path: Path) -> None:
        """Test detection of existing PDF files."""
        # Create a test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        result = detect_input_type(str(pdf_file))
        assert result == InputType.FILE

    def test_detect_non_pdf_file(self, tmp_path: Path) -> None:
        """Test rejection of non-PDF files."""
        # Create a non-PDF file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")

        with pytest.raises(ValidationError) as exc_info:
            detect_input_type(str(txt_file))

        assert "File must be a PDF" in str(exc_info.value)

    def test_detect_directory(self, tmp_path: Path) -> None:
        """Test detection of directories."""
        result = detect_input_type(str(tmp_path))
        assert result == InputType.DIRECTORY

    def test_detect_nonexistent_path(self) -> None:
        """Test rejection of nonexistent paths."""
        with pytest.raises(ValidationError) as exc_info:
            detect_input_type("/nonexistent/path")

        assert "Invalid input" in str(exc_info.value)

    def test_detect_file_no_extension(self, tmp_path: Path) -> None:
        """Test rejection of files without .pdf extension."""
        # Create a file without extension
        no_ext_file = tmp_path / "noextension"
        no_ext_file.write_text("content")

        with pytest.raises(ValidationError) as exc_info:
            detect_input_type(str(no_ext_file))

        assert "File must be a PDF" in str(exc_info.value)


class TestValidateDirectoryContainsPdfs:
    """Test directory PDF validation functionality."""

    def test_directory_with_pdfs(self, tmp_path: Path) -> None:
        """Test directory containing PDF files."""
        # Create PDF files
        pdf1 = tmp_path / "paper1.pdf"
        pdf2 = tmp_path / "paper2.pdf"
        pdf1.write_text("fake pdf 1")
        pdf2.write_text("fake pdf 2")

        result = validate_directory_contains_pdfs(tmp_path)

        assert len(result) == 2
        assert pdf1 in result
        assert pdf2 in result
        # Should be sorted
        assert result == sorted(result)

    def test_directory_no_pdfs(self, tmp_path: Path) -> None:
        """Test directory with no PDF files."""
        # Create non-PDF files
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("not a pdf")

        with pytest.raises(ValidationError) as exc_info:
            validate_directory_contains_pdfs(tmp_path)

        assert "No PDF files found" in str(exc_info.value)

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test empty directory."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_contains_pdfs(tmp_path)

        assert "No PDF files found" in str(exc_info.value)

    def test_directory_mixed_files(self, tmp_path: Path) -> None:
        """Test directory with mixed file types."""
        # Create mixed files
        pdf1 = tmp_path / "paper.pdf"
        txt1 = tmp_path / "readme.txt"
        pdf2 = tmp_path / "another.pdf"

        pdf1.write_text("fake pdf 1")
        txt1.write_text("text file")
        pdf2.write_text("fake pdf 2")

        result = validate_directory_contains_pdfs(tmp_path)

        # Should only return PDF files
        assert len(result) == 2
        assert pdf1 in result
        assert pdf2 in result
        assert txt1 not in result
