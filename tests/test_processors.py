# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Any
from unittest.mock import patch

from paperorganize.processors import (
    DirectoryProcessor,
    FileProcessor,
    ProcessingResult,
    URLProcessor,
)


class TestProcessingResult:
    """Test ProcessingResult data class."""

    def test_processing_result_creation(self, tmp_path: Path) -> None:
        """Test creating ProcessingResult."""
        original = tmp_path / "original.pdf"
        final = tmp_path / "final.pdf"

        result = ProcessingResult(
            original_path=original,
            final_path=final,
            was_downloaded=True,
            was_renamed=True,
        )

        assert result.original_path == original
        assert result.final_path == final
        assert result.was_downloaded is True
        assert result.was_renamed is True

    def test_processing_result_defaults(self, tmp_path: Path) -> None:
        """Test ProcessingResult default values."""
        original = tmp_path / "test.pdf"
        final = tmp_path / "test.pdf"

        result = ProcessingResult(
            original_path=original,
            final_path=final,
        )

        assert result.was_downloaded is False
        assert result.was_renamed is False


class TestURLProcessor:
    """Test URL processing functionality."""

    @patch("paperorganize.processors.download_file")
    @patch("paperorganize.metadata_naming.apply_metadata_naming")
    def test_url_processor_basic_download(
        self, mock_extract: Any, mock_download: Any, tmp_path: Path
    ) -> None:
        """Test basic URL download and processing."""
        # Setup mock to return a Path (since apply_metadata_naming returns a Path)
        temp_path = tmp_path / "Test_Paper.pdf"
        mock_extract.return_value = temp_path

        processor = URLProcessor()
        url = "https://example.com/paper.pdf"

        results = processor.process(
            url,
            tmp_path,
            None,
            auto_name=True,
            quiet=True,
        )

        assert len(results) == 1
        result = results[0]
        assert result.was_downloaded is True
        mock_download.assert_called_once()

    @patch("paperorganize.processors.download_file")
    def test_url_processor_custom_name(
        self, mock_download: Any, tmp_path: Path
    ) -> None:
        """Test URL download with custom filename."""
        processor = URLProcessor()
        url = "https://example.com/paper.pdf"
        custom_name = "custom_paper"

        results = processor.process(
            url,
            tmp_path,
            custom_name,
            auto_name=True,
            quiet=True,
        )

        assert len(results) == 1
        result = results[0]
        assert result.final_path.name == "custom_paper.pdf"

    def test_url_processor_filename_from_url(self) -> None:
        """Test filename extraction from URL."""
        processor = URLProcessor()

        # Test normal PDF URL
        filename = processor._determine_filename(None, "https://example.com/paper.pdf")
        assert filename == "paper.pdf"

        # Test URL without PDF extension
        filename = processor._determine_filename(None, "https://example.com/download")
        assert filename == "download.pdf"  # Preserve filename and add .pdf extension

        # Test arXiv URL - should get version from headers if available
        with patch("paperorganize.processors.get_download_info") as mock_get_info:
            # Mock successful header response with version number
            mock_get_info.return_value = ("1901.06032v7.pdf", True)
            filename = processor._determine_filename(
                None, "https://arxiv.org/pdf/1901.06032"
            )
            assert filename == "1901.06032v7.pdf"  # From Content-Disposition header

        # Test arXiv URL fallback when headers fail
        with patch("paperorganize.processors.get_download_info") as mock_get_info:
            # Mock header check failure with proper domain exception
            from paperorganize.exceptions import NetworkError

            mock_get_info.side_effect = NetworkError("Network error")
            filename = processor._determine_filename(
                None, "https://arxiv.org/pdf/1901.06032"
            )
            assert filename == "1901.06032.pdf"  # Fallback to URL parsing


class TestFileProcessor:
    """Test file processing functionality."""

    @patch("paperorganize.metadata_naming.apply_metadata_naming")
    def test_file_processor_same_directory(
        self, mock_extract: Any, tmp_path: Path
    ) -> None:
        """Test processing file in same directory."""
        # Create test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        # Setup mock to return a Path (since apply_metadata_naming returns a Path)
        renamed_path = tmp_path / "Test_Paper.pdf"
        mock_extract.return_value = renamed_path

        processor = FileProcessor()

        results = processor.process(
            str(pdf_file),
            tmp_path,
            None,
            auto_name=True,
            quiet=True,
        )

        assert len(results) == 1
        result = results[0]
        assert result.was_downloaded is False
        assert result.original_path == pdf_file

    def test_file_processor_copy_to_different_directory(self, tmp_path: Path) -> None:
        """Test copying file to different directory."""
        # Create source and destination directories
        source_dir = tmp_path / "source"
        dest_dir = tmp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create test PDF
        pdf_file = source_dir / "test.pdf"
        pdf_file.write_text("fake pdf content")

        processor = FileProcessor()

        results = processor.process(
            str(pdf_file),
            dest_dir,
            None,
            auto_name=False,  # No metadata processing for this test
            quiet=True,
        )

        assert len(results) == 1
        result = results[0]
        assert result.original_path == pdf_file
        assert result.final_path.parent == dest_dir
        assert (dest_dir / "test.pdf").exists()

    def test_file_processor_custom_name(self, tmp_path: Path) -> None:
        """Test file processing with custom name."""
        # Create test PDF
        pdf_file = tmp_path / "original.pdf"
        pdf_file.write_text("fake pdf content")

        processor = FileProcessor()

        results = processor.process(
            str(pdf_file),
            tmp_path,
            "custom_name",
            auto_name=False,
            quiet=True,
        )

        assert len(results) == 1
        result = results[0]
        assert result.final_path.name == "custom_name.pdf"


class TestDirectoryProcessor:
    """Test directory processing functionality."""

    @patch("paperorganize.processors.validate_directory_contains_pdfs")
    def test_directory_processor_multiple_files(
        self, mock_validate: Any, tmp_path: Path
    ) -> None:
        """Test processing directory with multiple PDF files."""
        # Create test PDFs
        pdf1 = tmp_path / "paper1.pdf"
        pdf2 = tmp_path / "paper2.pdf"
        pdf1.write_text("fake pdf 1")
        pdf2.write_text("fake pdf 2")

        # Mock validation to return our test files
        mock_validate.return_value = [pdf1, pdf2]

        processor = DirectoryProcessor()

        with patch.object(FileProcessor, "process") as mock_file_process:
            # Mock file processor to return simple results
            mock_file_process.side_effect = [
                [ProcessingResult(pdf1, pdf1, was_downloaded=False, was_renamed=False)],
                [ProcessingResult(pdf2, pdf2, was_downloaded=False, was_renamed=False)],
            ]

            results = processor.process(
                str(tmp_path),
                tmp_path,
                None,
                auto_name=True,
                quiet=True,
            )

        assert len(results) == 2
        # Should have called file processor for each PDF
        assert mock_file_process.call_count == 2

    @patch("paperorganize.processors.validate_directory_contains_pdfs")
    def test_directory_processor_ignores_custom_name(
        self, mock_validate: Any, tmp_path: Path
    ) -> None:
        """Test that directory processing ignores custom name in batch mode."""
        # Create test PDF
        pdf1 = tmp_path / "paper1.pdf"
        pdf1.write_text("fake pdf 1")

        mock_validate.return_value = [pdf1]

        processor = DirectoryProcessor()

        with patch.object(FileProcessor, "process") as mock_file_process:
            mock_file_process.return_value = [
                ProcessingResult(pdf1, pdf1, was_downloaded=False, was_renamed=False)
            ]

            processor.process(
                str(tmp_path),
                tmp_path,
                "should_be_ignored",
                auto_name=True,
                quiet=True,
            )

            # Verify custom_name was set to None in the call
            mock_file_process.assert_called_once()
            call_args = mock_file_process.call_args
            assert call_args[1]["custom_name"] is None
