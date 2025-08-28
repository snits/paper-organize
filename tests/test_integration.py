# ABOUTME: Reliable integration tests using local HTTP server infrastructure
# ABOUTME: Tests complete unified processing pipeline without external service dependencies
# SPDX-License-Identifier: MIT

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from click.testing import CliRunner
from pytest_httpserver import HTTPServer

from paperorganize.cli import main

from .http_test_helpers import setup_error_response, setup_pdf_response


class TestCLIIntegrationReliable:
    """Reliable integration tests using local HTTP server."""

    def test_successful_download_with_local_server(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes, temp_dir: Path
    ) -> None:
        """Test successful download using local HTTP server with controlled PDF content."""
        runner = CliRunner()

        # Set up server to return PDF content
        test_url = setup_pdf_response(
            http_server, "/test.pdf", pdf_fixture_minimal, filename="test_download.pdf"
        )

        result = runner.invoke(
            main, [test_url, "--dir", str(temp_dir), "--name", "test_download.pdf"]
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"
        assert f"→ Downloading from URL: {test_url}" in result.output
        assert "✓ Downloaded to:" in result.output

        # Verify file was created with correct content
        downloaded_file = temp_dir / "test_download.pdf"
        assert downloaded_file.exists(), f"Expected file not created: {downloaded_file}"
        assert downloaded_file.read_bytes() == pdf_fixture_minimal

    def test_http_404_error_handling(
        self, http_server: HTTPServer, temp_dir: Path
    ) -> None:
        """Test CLI handles HTTP 404 errors gracefully."""
        runner = CliRunner()

        # Set up server to return 404
        test_url = setup_error_response(
            http_server, "/missing.pdf", 404, error_message="Not Found"
        )

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code != 0
        assert "✗ HTTP 404:" in result.output
        assert "→ Downloading from URL:" in result.output

        # Verify no file was created
        assert not any(temp_dir.glob("*")), (
            f"Unexpected files created: {list(temp_dir.glob('*'))}"
        )

    def test_http_500_error_handling(
        self, http_server: HTTPServer, temp_dir: Path
    ) -> None:
        """Test CLI handles HTTP 500 errors gracefully."""
        runner = CliRunner()

        # Set up server to return 500
        test_url = setup_error_response(
            http_server, "/error.pdf", 500, error_message="Internal Server Error"
        )

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code != 0
        assert "✗ HTTP 500:" in result.output

    def test_default_filename_generation(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes, temp_dir: Path
    ) -> None:
        """Test CLI generates appropriate default filenames."""
        runner = CliRunner()

        # Set up server with URL that doesn't end in .pdf
        test_url = setup_pdf_response(
            http_server, "/data", pdf_fixture_minimal, content_type="application/pdf"
        )

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should create a PDF file (exact name depends on URL processing logic)
        created_files = list(temp_dir.glob("*.pdf"))
        assert len(created_files) >= 1, (
            f"No PDF files created, found: {list(temp_dir.glob('*'))}"
        )

        # Verify content is correct regardless of filename
        created_file = created_files[0]
        assert created_file.read_bytes() == pdf_fixture_minimal

    def test_large_file_download_with_progress(
        self, http_server: HTTPServer, large_pdf_content: bytes, temp_dir: Path
    ) -> None:
        """Test downloading larger file to verify chunked download works."""
        runner = CliRunner()

        test_url = setup_pdf_response(http_server, "/large.pdf", large_pdf_content)

        result = runner.invoke(
            main, [test_url, "--dir", str(temp_dir), "--name", "large_test.pdf"]
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        downloaded_file = temp_dir / "large_test.pdf"
        assert downloaded_file.exists()
        assert len(downloaded_file.read_bytes()) == len(large_pdf_content)

    def test_quiet_mode_suppresses_output(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes, temp_dir: Path
    ) -> None:
        """Test --quiet flag suppresses non-error output."""
        runner = CliRunner()

        test_url = setup_pdf_response(http_server, "/quiet.pdf", pdf_fixture_minimal)

        result = runner.invoke(
            main,
            [test_url, "--dir", str(temp_dir), "--name", "quiet_test.pdf", "--quiet"],
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"
        # Should not contain download messages
        assert "→ Downloading:" not in result.output
        assert "✓ Downloaded to:" not in result.output

        # But file should still be created
        downloaded_file = temp_dir / "quiet_test.pdf"
        assert downloaded_file.exists()

    def test_custom_directory_creation(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes, temp_dir: Path
    ) -> None:
        """Test CLI creates custom directories as needed."""
        runner = CliRunner()

        custom_dir = temp_dir / "papers" / "subdir"
        test_url = setup_pdf_response(http_server, "/paper.pdf", pdf_fixture_minimal)

        result = runner.invoke(
            main, [test_url, "--dir", str(custom_dir), "--name", "custom_dir_test.pdf"]
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"
        assert custom_dir.exists(), f"Custom directory not created: {custom_dir}"

        downloaded_file = custom_dir / "custom_dir_test.pdf"
        assert downloaded_file.exists(), (
            f"File not created in custom directory: {downloaded_file}"
        )

    def test_automatic_pdf_extension(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes, temp_dir: Path
    ) -> None:
        """Test CLI automatically adds .pdf extension to custom names."""
        runner = CliRunner()

        test_url = setup_pdf_response(http_server, "/paper.pdf", pdf_fixture_minimal)

        result = runner.invoke(
            main, [test_url, "--dir", str(temp_dir), "--name", "no_extension"]
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should create file with .pdf extension
        downloaded_file = temp_dir / "no_extension.pdf"
        assert downloaded_file.exists(), (
            f"File with .pdf extension not created: {downloaded_file}"
        )

    @patch("paperorganize.download.requests.get")
    def test_connection_timeout_handling(
        self, mock_get: MagicMock, temp_dir: Path
    ) -> None:
        """Test CLI handles connection timeouts gracefully."""
        runner = CliRunner()

        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = runner.invoke(
            main, ["http://example.com/test.pdf", "--dir", str(temp_dir)]
        )

        assert result.exit_code != 0
        assert "✗ Network error:" in result.output
        assert "timed out" in result.output.lower()

    def test_connection_error_handling(self, temp_dir: Path) -> None:
        """Test CLI handles connection errors gracefully."""
        runner = CliRunner()

        # Use a non-existent domain to trigger connection error
        test_url = "https://this-domain-definitely-does-not-exist-12345.com/file.pdf"

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code != 0
        assert "✗ Network error:" in result.output
        # Connection errors can have various messages depending on system
        assert any(
            phrase in result.output
            for phrase in [
                "Connection failed",
                "Name or service not known",
                "nodename nor servname provided",
            ]
        )

    def test_invalid_url_validation(self, temp_dir: Path) -> None:
        """Test CLI validates URLs properly."""
        runner = CliRunner()

        invalid_urls = ["ftp://example.com/file.pdf", "http://", "not-a-url-at-all"]

        for invalid_url in invalid_urls:
            result = runner.invoke(main, [invalid_url, "--dir", str(temp_dir)])

            assert result.exit_code != 0, (
                f"Should have failed for invalid URL: {invalid_url}"
            )
            assert "✗" in result.output

    def test_nonexistent_path_validation(self, temp_dir: Path) -> None:
        """Test CLI validates non-existent paths properly."""
        runner = CliRunner()

        nonexistent_paths = ["/nonexistent/path/file.pdf", "missing_file.pdf"]

        for path in nonexistent_paths:
            result = runner.invoke(main, [path, "--dir", str(temp_dir)])

            assert result.exit_code != 0, (
                f"Should have failed for non-existent path: {path}"
            )
            assert "✗" in result.output


class TestCLIMetadataIntegrationReliable:
    """Integration tests for metadata extraction without external dependencies."""

    def test_auto_naming_with_valid_pdf(
        self, http_server: HTTPServer, pdf_fixture_with_metadata: bytes, temp_dir: Path
    ) -> None:
        """Test auto-naming works with PDF containing metadata."""
        runner = CliRunner()

        test_url = setup_pdf_response(
            http_server, "/paper.pdf", pdf_fixture_with_metadata
        )

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should create file and attempt metadata extraction
        created_files = list(temp_dir.glob("*.pdf"))
        assert len(created_files) == 1, f"Expected 1 PDF file, found: {created_files}"

    def test_auto_naming_disabled_with_flag(
        self, http_server: HTTPServer, pdf_fixture_with_metadata: bytes, temp_dir: Path
    ) -> None:
        """Test --no-auto-name flag disables metadata-based renaming."""
        runner = CliRunner()

        test_url = setup_pdf_response(
            http_server, "/paper.pdf", pdf_fixture_with_metadata
        )

        result = runner.invoke(
            main, [test_url, "--dir", str(temp_dir), "--no-auto-name"]
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should create file without metadata renaming
        created_files = list(temp_dir.glob("*.pdf"))
        assert len(created_files) == 1, f"Expected 1 PDF file, found: {created_files}"
        # Should not show metadata extraction output
        assert "✓ Renamed to:" not in result.output

    def test_auto_naming_disabled_with_custom_name(
        self, http_server: HTTPServer, pdf_fixture_with_metadata: bytes, temp_dir: Path
    ) -> None:
        """Test that custom --name disables auto-naming."""
        runner = CliRunner()

        custom_name = "my_custom_paper.pdf"
        test_url = setup_pdf_response(
            http_server, "/paper.pdf", pdf_fixture_with_metadata
        )

        result = runner.invoke(
            main, [test_url, "--dir", str(temp_dir), "--name", custom_name]
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should keep custom filename
        custom_file = temp_dir / custom_name
        assert custom_file.exists(), f"Custom named file not created: {custom_file}"

        # Should not show metadata extraction output since custom name provided
        assert "✓ Renamed to:" not in result.output

    @patch("paperorganize.processors.apply_metadata_naming")
    def test_auto_naming_with_metadata_success(
        self,
        mock_extract: MagicMock,
        http_server: HTTPServer,
        pdf_fixture_minimal: bytes,
        temp_dir: Path,
    ) -> None:
        """Test successful auto-naming when metadata is available."""
        runner = CliRunner()

        def mock_rename(file_path: Path, *, quiet: bool = False) -> Path:
            """Mock that renames the file and returns the new path."""
            new_path = file_path.parent / "Smith_2024_Machine_Learning_Survey.pdf"
            file_path.rename(new_path)
            return new_path

        mock_extract.side_effect = mock_rename

        test_url = setup_pdf_response(http_server, "/paper.pdf", pdf_fixture_minimal)

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should create file with metadata-based name
        expected_file = temp_dir / "Smith_2024_Machine_Learning_Survey.pdf"
        assert expected_file.exists(), f"Renamed file not found: {expected_file}"

    @patch("paperorganize.processors.apply_metadata_naming")
    def test_auto_naming_falls_back_on_extraction_failure(
        self,
        mock_extract: MagicMock,
        http_server: HTTPServer,
        pdf_fixture_minimal: bytes,
        temp_dir: Path,
    ) -> None:
        """Test that auto-naming falls back gracefully when metadata extraction fails."""
        runner = CliRunner()

        def mock_exception(file_path: Path, *, quiet: bool = False) -> Path:
            """Mock that returns original path when extraction fails."""
            return file_path

        mock_extract.side_effect = mock_exception

        test_url = setup_pdf_response(http_server, "/paper.pdf", pdf_fixture_minimal)

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir)])

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should create file (exact name depends on processing logic)
        created_files = list(temp_dir.glob("*.pdf"))
        assert len(created_files) == 1, f"Expected 1 PDF file, found: {created_files}"

    def test_quiet_mode_suppresses_metadata_output(
        self, http_server: HTTPServer, pdf_fixture_with_metadata: bytes, temp_dir: Path
    ) -> None:
        """Test that --quiet flag suppresses metadata extraction messages."""
        runner = CliRunner()

        test_url = setup_pdf_response(
            http_server, "/paper.pdf", pdf_fixture_with_metadata
        )

        result = runner.invoke(main, [test_url, "--dir", str(temp_dir), "--quiet"])

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Should not show any output in quiet mode
        assert result.output.strip() == ""

        # File should still be created (with or without renaming)
        files = list(temp_dir.glob("*.pdf"))
        assert len(files) == 1, f"Expected 1 PDF file, found: {files}"


class TestCLIFileSystemErrorsReliable:
    """Integration tests for file system error scenarios."""

    def test_permission_denied_directory(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes
    ) -> None:
        """Test CLI handles permission denied errors gracefully."""
        runner = CliRunner()

        # Create temporary directory and make it read-only
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only

            test_url = setup_pdf_response(
                http_server, "/paper.pdf", pdf_fixture_minimal
            )

            try:
                result = runner.invoke(
                    main, [test_url, "--dir", str(readonly_dir), "--name", "test.pdf"]
                )

                # Should fail with file system error
                assert result.exit_code != 0
                assert "✗" in result.output

            finally:
                # Restore permissions for cleanup
                readonly_dir.chmod(0o755)


class TestCLIProgressAndOutputReliable:
    """Integration tests for CLI output and progress handling."""

    def test_verbose_mode_output(
        self, http_server: HTTPServer, pdf_fixture_minimal: bytes, temp_dir: Path
    ) -> None:
        """Test --verbose flag provides detailed output."""
        runner = CliRunner()

        test_url = setup_pdf_response(http_server, "/paper.pdf", pdf_fixture_minimal)

        result = runner.invoke(
            main,
            [
                test_url,
                "--dir",
                str(temp_dir),
                "--name",
                "verbose_test.pdf",
                "--verbose",
            ],
        )

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"
        assert "→ Downloading from URL:" in result.output
        assert "✓ Downloaded to:" in result.output

        # File should be created
        downloaded_file = temp_dir / "verbose_test.pdf"
        assert downloaded_file.exists()


# Performance benchmark test (optional, can be slow)
@pytest.mark.slow
class TestPerformanceReliable:
    """Performance tests for download functionality."""

    def test_download_speed_reasonable(
        self, http_server: HTTPServer, temp_dir: Path
    ) -> None:
        """Test that local downloads complete quickly."""
        runner = CliRunner()

        # Create 1MB of test data
        large_content = b"X" * (1024 * 1024)
        test_url = setup_pdf_response(http_server, "/large.pdf", large_content)

        start_time = time.time()
        result = runner.invoke(
            main, [test_url, "--dir", str(temp_dir), "--name", "speed_test.pdf"]
        )
        end_time = time.time()

        assert result.exit_code == 0
        # Local downloads should be very fast (under 5 seconds even for 1MB)
        assert end_time - start_time < 5.0, (
            f"Download took too long: {end_time - start_time:.2f}s"
        )

        downloaded_file = temp_dir / "speed_test.pdf"
        assert downloaded_file.exists()
        assert len(downloaded_file.read_bytes()) == len(large_content)
