# ABOUTME: Download module tests for basic HTTP functionality
# ABOUTME: Tests basic file downloading and error handling

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from paperdl.download import download_file

# Test constants
TEST_FILE_SIZE = 1024


def test_download_file_basic_functionality():
    """Test basic download functionality with real HTTP endpoint."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test_download.bin"

        # Use httpbin.org for reliable testing - download 1KB of random data
        url = f"https://httpbin.org/bytes/{TEST_FILE_SIZE}"

        result = download_file(url, str(dest_path))

        # Verify download succeeded
        assert result is True
        # Verify file was created
        assert dest_path.exists()
        # Verify file has expected size (1024 bytes)
        assert dest_path.stat().st_size == TEST_FILE_SIZE
        # Verify file contains binary data
        with dest_path.open("rb") as f:
            content = f.read()
            assert len(content) == TEST_FILE_SIZE
            assert isinstance(content, bytes)


def test_download_file_success():
    """Test successful file download."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Mock requests to avoid actual HTTP calls
        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "1000"}
            mock_response.iter_content.return_value = [b"test data"]
            mock_get.return_value = mock_response

            result = download_file("https://example.com/test.pdf", str(dest_path))

            assert result is True
            assert dest_path.exists()
            with dest_path.open("rb") as f:
                assert f.read() == b"test data"


def test_download_file_http_error():
    """Test download with HTTP error response."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value = mock_response

            result = download_file("https://example.com/missing.pdf", str(dest_path))

            assert result is False
            assert not dest_path.exists()


def test_download_file_network_timeout():
    """Test download with network timeout."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        with patch("paperdl.download.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

            result = download_file("https://slow.example.com/test.pdf", str(dest_path))

            assert result is False
            assert not dest_path.exists()


def test_download_file_creates_directory():
    """Test that download creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = Path(temp_dir) / "nested" / "dir" / "test.pdf"

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "500"}
            mock_response.iter_content.return_value = [b"pdf content"]
            mock_get.return_value = mock_response

            result = download_file("https://example.com/test.pdf", str(nested_path))

            assert result is True
            assert nested_path.exists()
            assert nested_path.parent.exists()


# TODO(claude): Progress callback tests will be added in future atomic commit
# TODO(claude): Retry logic tests will be added in future atomic commit


