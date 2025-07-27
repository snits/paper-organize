# ABOUTME: Integration tests for paper-dl CLI with real network calls
# ABOUTME: Tests complete CLI-to-download pipeline using httpbin.org for reliable testing
# SPDX-License-Identifier: MIT

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests
from click.testing import CliRunner

from paperdl.cli import main
from paperdl.metadata import PaperMetadata


class TestCLIIntegration:
    """Integration tests for CLI functionality with real network calls."""

    def setup_method(self) -> None:
        """Set up test environment with temporary directory."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        # Clean up any downloaded files
        if self.temp_path.exists():
            # Remove all files first
            for file in self.temp_path.rglob("*"):
                if file.is_file():
                    file.unlink()
            # Remove directories (in reverse order for nested dirs)
            for directory in sorted(
                self.temp_path.rglob("*"), key=lambda p: len(str(p)), reverse=True
            ):
                if directory.is_dir():
                    directory.rmdir()
            # Finally remove the temp directory itself
            self.temp_path.rmdir()

    def test_successful_download_with_real_http_endpoint(self) -> None:
        """Test successful download using httpbin.org which returns PDF-like content."""
        # httpbin.org/bytes/1024 returns exactly 1024 bytes of binary data
        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(self.temp_path), "--name", "test_file.pdf"]
        )

        assert result.exit_code == 0
        assert f"→ Downloading: {test_url}" in result.output
        assert "✓ Downloaded to:" in result.output

        # Verify file was actually created and has correct size
        downloaded_file = self.temp_path / "test_file.pdf"
        assert downloaded_file.exists()
        assert downloaded_file.stat().st_size == 1024  # noqa: PLR2004

    def test_http_404_error_handling(self) -> None:
        """Test CLI handles HTTP 404 errors gracefully."""
        test_url = "https://httpbin.org/status/404"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code != 0
        assert "✗ HTTP 404:" in result.output
        assert "→ Downloading:" in result.output

        # Verify no file was created
        assert not any(self.temp_path.glob("*"))

    def test_http_500_error_handling(self) -> None:
        """Test CLI handles HTTP 500 errors gracefully."""
        test_url = "https://httpbin.org/status/500"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code != 0
        assert "✗ HTTP 500:" in result.output
        assert "→ Downloading:" in result.output

    def test_network_timeout_error_handling(self) -> None:
        """Test CLI handles network timeout errors gracefully."""
        # Use a mock to force a timeout since httpbin delays might be unreliable
        with patch("paperdl.download.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            test_url = "https://httpbin.org/bytes/1024"

            result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

            assert result.exit_code != 0
            assert "✗ Network error:" in result.output
            assert "timed out" in result.output

    def test_invalid_url_validation(self) -> None:
        """Test CLI validates URLs properly."""
        invalid_urls = ["not-a-url", "ftp://example.com/file.pdf", "http://", ""]

        for invalid_url in invalid_urls:
            result = self.runner.invoke(
                main, [invalid_url, "--dir", str(self.temp_path)]
            )

            assert result.exit_code != 0
            assert "✗" in result.output

    def test_quiet_mode_suppresses_output(self) -> None:
        """Test --quiet flag suppresses non-error output."""
        test_url = "https://httpbin.org/bytes/512"

        result = self.runner.invoke(
            main,
            [
                test_url,
                "--dir",
                str(self.temp_path),
                "--name",
                "quiet_test.pdf",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        # Should not contain download messages
        assert "→ Downloading:" not in result.output
        assert "✓ Downloaded to:" not in result.output

        # But file should still be created
        downloaded_file = self.temp_path / "quiet_test.pdf"
        assert downloaded_file.exists()

    def test_custom_directory_creation(self) -> None:
        """Test CLI creates custom directories as needed."""
        custom_dir = self.temp_path / "papers" / "subdir"
        test_url = "https://httpbin.org/bytes/256"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(custom_dir), "--name", "custom_dir_test.pdf"]
        )

        assert result.exit_code == 0
        assert custom_dir.exists()

        downloaded_file = custom_dir / "custom_dir_test.pdf"
        assert downloaded_file.exists()
        assert downloaded_file.stat().st_size == 256  # noqa: PLR2004

    def test_automatic_pdf_extension(self) -> None:
        """Test CLI automatically adds .pdf extension to custom names."""
        test_url = "https://httpbin.org/bytes/128"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(self.temp_path), "--name", "no_extension"]
        )

        assert result.exit_code == 0

        # Should create file with .pdf extension
        downloaded_file = self.temp_path / "no_extension.pdf"
        assert downloaded_file.exists()
        assert downloaded_file.stat().st_size == 128  # noqa: PLR2004

    def test_default_filename_generation(self) -> None:
        """Test CLI generates appropriate default filenames."""
        # URL that doesn't end in .pdf
        test_url = "https://httpbin.org/bytes/64"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code == 0

        # Should create paper.pdf as default
        downloaded_file = self.temp_path / "paper.pdf"
        assert downloaded_file.exists()
        assert downloaded_file.stat().st_size == 64  # noqa: PLR2004

    def test_connection_error_handling(self) -> None:
        """Test CLI handles connection errors gracefully."""
        # Use a non-existent domain to trigger connection error
        test_url = "https://this-domain-does-not-exist-12345.com/file.pdf"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code != 0
        assert "✗ Network error:" in result.output
        assert (
            "Connection failed" in result.output
            or "Name or service not known" in result.output
        )


class TestCLIFileSystemErrors:
    """Integration tests for file system error scenarios."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_permission_denied_directory(self) -> None:
        """Test CLI handles permission denied errors gracefully."""
        # Try to write to a read-only directory (if we can create one)
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only

            test_url = "https://httpbin.org/bytes/64"

            result = self.runner.invoke(
                main, [test_url, "--dir", str(readonly_dir), "--name", "test.pdf"]
            )

            # Should fail with file system error
            assert result.exit_code != 0
            assert "✗" in result.output

            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)


class TestCLIProgressAndOutput:
    """Integration tests for CLI output and progress handling."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        if self.temp_path.exists():
            # Remove all files first
            for file in self.temp_path.rglob("*"):
                if file.is_file():
                    file.unlink()
            # Remove directories (in reverse order for nested dirs)
            for directory in sorted(
                self.temp_path.rglob("*"), key=lambda p: len(str(p)), reverse=True
            ):
                if directory.is_dir():
                    directory.rmdir()
            # Finally remove the temp directory itself
            self.temp_path.rmdir()

    def test_verbose_mode_output(self) -> None:
        """Test --verbose flag provides detailed output."""
        test_url = "https://httpbin.org/bytes/256"

        result = self.runner.invoke(
            main,
            [
                test_url,
                "--dir",
                str(self.temp_path),
                "--name",
                "verbose_test.pdf",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "→ Downloading:" in result.output
        assert "✓ Downloaded to:" in result.output

        # File should be created
        downloaded_file = self.temp_path / "verbose_test.pdf"
        assert downloaded_file.exists()

    def test_large_file_download(self) -> None:
        """Test downloading a larger file to ensure chunked download works."""
        # Download 10KB file to test chunked downloading
        test_url = "https://httpbin.org/bytes/10240"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(self.temp_path), "--name", "large_test.pdf"]
        )

        assert result.exit_code == 0

        downloaded_file = self.temp_path / "large_test.pdf"
        assert downloaded_file.exists()
        assert downloaded_file.stat().st_size == 10240  # noqa: PLR2004


class TestCLIMetadataIntegration:
    """Integration tests for CLI metadata extraction and auto-naming functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        if self.temp_path.exists():
            # Remove all files first
            for file in self.temp_path.rglob("*"):
                if file.is_file():
                    file.unlink()
            # Remove directories (in reverse order for nested dirs)
            for directory in sorted(
                self.temp_path.rglob("*"), key=lambda p: len(str(p)), reverse=True
            ):
                if directory.is_dir():
                    directory.rmdir()
            # Finally remove the temp directory itself
            self.temp_path.rmdir()

    def test_auto_naming_disabled_with_flag(self) -> None:
        """Test that --no-auto-name flag disables metadata-based renaming."""
        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(self.temp_path), "--no-auto-name"]
        )

        assert result.exit_code == 0

        # Should keep default filename (paper.pdf)
        default_file = self.temp_path / "paper.pdf"
        assert default_file.exists()

        # Should not show metadata extraction output
        assert "✓ Renamed to:" not in result.output

    def test_auto_naming_disabled_with_custom_name(self) -> None:
        """Test that custom --name disables auto-naming."""
        test_url = "https://httpbin.org/bytes/1024"
        custom_name = "my_custom_paper.pdf"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(self.temp_path), "--name", custom_name]
        )

        assert result.exit_code == 0

        # Should keep custom filename
        custom_file = self.temp_path / custom_name
        assert custom_file.exists()

        # Should not show metadata extraction output since custom name provided
        assert "✓ Renamed to:" not in result.output

    @patch("paperdl.cli.extract_pdf_metadata")
    def test_auto_naming_with_metadata_success(self, mock_extract: MagicMock) -> None:
        """Test successful auto-naming when metadata is available."""

        # Mock metadata extraction to return structured data
        mock_extract.return_value = PaperMetadata(
            title="Machine Learning Survey",
            authors=["John Smith", "Jane Doe"],
            year=2024,
        )

        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code == 0

        # Should create file with metadata-based name
        expected_file = self.temp_path / "Smith_2024_Machine_Learning_Survey.pdf"
        assert expected_file.exists()

        # Should show renaming output
        assert "✓ Renamed to: Smith_2024_Machine_Learning_Survey.pdf" in result.output

        # Original paper.pdf should not exist
        original_file = self.temp_path / "paper.pdf"
        assert not original_file.exists()

    @patch("paperdl.cli.extract_pdf_metadata")
    def test_auto_naming_with_partial_metadata(self, mock_extract: MagicMock) -> None:
        """Test auto-naming with partial metadata (title only)."""

        # Mock metadata extraction with only title
        mock_extract.return_value = PaperMetadata(
            title="Deep Learning Fundamentals", authors=[], year=None
        )

        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code == 0

        # Should create file with title-only name
        expected_file = self.temp_path / "Deep_Learning_Fundamentals.pdf"
        assert expected_file.exists()

        # Should show renaming output
        assert "✓ Renamed to: Deep_Learning_Fundamentals.pdf" in result.output

    @patch("paperdl.cli.extract_pdf_metadata")
    def test_auto_naming_falls_back_on_extraction_failure(
        self, mock_extract: MagicMock
    ) -> None:
        """Test that auto-naming falls back gracefully when metadata extraction fails."""
        # Mock metadata extraction to raise an exception
        mock_extract.side_effect = Exception("PDF parsing failed")

        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code == 0

        # Should keep original filename
        original_file = self.temp_path / "paper.pdf"
        assert original_file.exists()

        # Should show warning message
        assert "⚠ Could not extract metadata for intelligent naming" in result.output

        # Should not show renaming output
        assert "✓ Renamed to:" not in result.output

    @patch("paperdl.cli.extract_pdf_metadata")
    def test_auto_naming_handles_filename_conflicts(
        self, mock_extract: MagicMock
    ) -> None:
        """Test that auto-naming handles filename conflicts by adding numbers."""

        # Mock metadata extraction
        mock_extract.return_value = PaperMetadata(
            title="Conflict Test", authors=["Test Author"], year=2024
        )

        # Pre-create file with the expected name to create conflict
        conflicting_file = self.temp_path / "Author_2024_Conflict_Test.pdf"
        conflicting_file.write_text("existing file")

        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(main, [test_url, "--dir", str(self.temp_path)])

        assert result.exit_code == 0

        # Should create file with conflict resolution suffix
        resolved_file = self.temp_path / "Author_2024_Conflict_Test_1.pdf"
        assert resolved_file.exists()

        # Original conflicting file should still exist
        assert conflicting_file.exists()

        # Should show renaming output with resolved name
        assert "✓ Renamed to: Author_2024_Conflict_Test_1.pdf" in result.output

    def test_quiet_mode_suppresses_metadata_output(self) -> None:
        """Test that --quiet flag suppresses metadata extraction messages."""
        test_url = "https://httpbin.org/bytes/1024"

        result = self.runner.invoke(
            main, [test_url, "--dir", str(self.temp_path), "--quiet"]
        )

        assert result.exit_code == 0

        # Should not show any output in quiet mode
        assert result.output.strip() == ""

        # File should still be created (with or without renaming)
        files = list(self.temp_path.glob("*.pdf"))
        assert len(files) == 1
