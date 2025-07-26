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


def test_download_file_progress_callback_with_content_length():
    """Test progress callback with known Content-Length."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Track progress calls
        progress_calls = []

        def progress_callback(bytes_downloaded: int, total_bytes: int) -> None:
            progress_calls.append((bytes_downloaded, total_bytes))

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "16"}  # Two 8-byte chunks
            # Return chunks that sum to 16 bytes
            mock_response.iter_content.return_value = [b"chunk001", b"chunk002"]
            mock_get.return_value = mock_response

            result = download_file("https://example.com/test.pdf", str(dest_path), progress_callback)

            assert result is True
            assert dest_path.exists()

            # Verify progress was tracked correctly
            assert len(progress_calls) == 2  # noqa: PLR2004
            assert progress_calls[0] == (8, 16)  # First chunk: 8 bytes downloaded, 16 total
            assert progress_calls[1] == (16, 16)  # Second chunk: 16 bytes downloaded, 16 total


def test_download_file_progress_callback_without_content_length():
    """Test progress callback when Content-Length header is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Track progress calls
        progress_calls = []

        def progress_callback(bytes_downloaded: int, total_bytes: int) -> None:
            progress_calls.append((bytes_downloaded, total_bytes))

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}  # No Content-Length header
            mock_response.iter_content.return_value = [b"data1", b"data2", b"data3"]
            mock_get.return_value = mock_response

            result = download_file("https://example.com/test.pdf", str(dest_path), progress_callback)

            assert result is True
            assert dest_path.exists()

            # Verify progress was tracked with -1 for unknown total
            assert len(progress_calls) == 3  # noqa: PLR2004
            assert progress_calls[0] == (5, -1)   # 5 bytes downloaded, unknown total
            assert progress_calls[1] == (10, -1)  # 10 bytes downloaded, unknown total
            assert progress_calls[2] == (15, -1)  # 15 bytes downloaded, unknown total


def test_download_file_progress_callback_invalid_content_length():
    """Test progress callback when Content-Length header is invalid."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Track progress calls
        progress_calls = []

        def progress_callback(bytes_downloaded: int, total_bytes: int) -> None:
            progress_calls.append((bytes_downloaded, total_bytes))

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "not-a-number"}  # Invalid content length
            mock_response.iter_content.return_value = [b"testdata"]
            mock_get.return_value = mock_response

            result = download_file("https://example.com/test.pdf", str(dest_path), progress_callback)

            assert result is True
            assert dest_path.exists()

            # Verify progress was tracked with -1 for invalid total
            assert len(progress_calls) == 1
            assert progress_calls[0] == (8, -1)  # 8 bytes downloaded, invalid total treated as unknown


def test_download_file_no_progress_callback():
    """Test that download works normally when no progress callback is provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "100"}
            mock_response.iter_content.return_value = [b"test data"]
            mock_get.return_value = mock_response

            # Call without progress callback (None is the default)
            result = download_file("https://example.com/test.pdf", str(dest_path))

            assert result is True
            assert dest_path.exists()
            with dest_path.open("rb") as f:
                assert f.read() == b"test data"


def test_download_file_progress_callback_error_handling():
    """Test that callback errors don't break the download."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        def failing_callback(_bytes_downloaded: int, _total_bytes: int) -> None:
            msg = "Callback failed!"
            raise RuntimeError(msg)

        with patch("paperdl.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "9"}
            mock_response.iter_content.return_value = [b"test data"]
            mock_get.return_value = mock_response

            # The download should succeed despite callback failure
            # Callback errors should not break the download
            result = download_file("https://example.com/test.pdf", str(dest_path), failing_callback)

            assert result is True
            assert dest_path.exists()
            # Verify file content was still written correctly
            assert dest_path.read_bytes() == b"test data"


# TODO(claude): Retry logic tests will be added in future atomic commit


