# ABOUTME: Download module tests for basic HTTP functionality
# ABOUTME: Tests basic file downloading and error handling
# SPDX-License-Identifier: MIT

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from paperorganize.download import (
    _extract_filename_from_content_disposition,
    _is_pdf_content_type,
    calculate_retry_delay,
    download_file,
    get_download_info,
    with_retry,
)
from paperorganize.exceptions import HTTPError, NetworkError

# Test constants
TEST_FILE_SIZE = 1024
HTTP_NOT_FOUND = 404
MAX_RETRY_ATTEMPTS = 3
RETRY_ATTEMPTS_MINUS_ONE = 2
INITIAL_DELAY = 1.0
SECOND_DELAY = 2.0
FIRST_ATTEMPT = 1

# Exception messages for tests
TIMEOUT_MSG = "Connection timeout"
ALWAYS_FAILS_MSG = "Always fails"
NO_RETRY_MSG = "This should not be retried"
IMMEDIATE_FAILURE_MSG = "Immediate failure"
NO_RETRY_EXPECTED_MSG = "Should not be retried"
FIRST_FAILURE_MSG = "First failure"
SECOND_FAILURE_MSG = "Second failure"



def test_download_file_success() -> None:
    """Test successful file download."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Mock requests to avoid actual HTTP calls
        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "9"}  # Match actual data size
            mock_response.iter_content.return_value = [b"test data"]
            mock_get.return_value = mock_response

            download_file("https://example.com/test.pdf", str(dest_path))
            assert dest_path.exists()
            with dest_path.open("rb") as f:
                assert f.read() == b"test data"


def test_download_file_http_error() -> None:
    """Test download with HTTP error response."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = HTTP_NOT_FOUND
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "404 Not Found"
            )
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError) as exc_info:
                download_file("https://example.com/missing.pdf", str(dest_path))

            assert "HTTP request failed" in str(exc_info.value)
            assert exc_info.value.status_code == HTTP_NOT_FOUND
            assert not dest_path.exists()


def test_download_file_network_timeout() -> None:
    """Test download with network timeout."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

            with pytest.raises(NetworkError) as exc_info:
                download_file("https://slow.example.com/test.pdf", str(dest_path))

            assert "Request timed out" in str(exc_info.value)
            assert not dest_path.exists()


def test_download_file_creates_directory() -> None:
    """Test that download creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = Path(temp_dir) / "nested" / "dir" / "test.pdf"

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "11"}  # Match "pdf content" size
            mock_response.iter_content.return_value = [b"pdf content"]
            mock_get.return_value = mock_response

            download_file("https://example.com/test.pdf", str(nested_path))

            assert nested_path.exists()
            assert nested_path.parent.exists()


def test_download_file_progress_callback_with_content_length() -> None:
    """Test progress callback with known Content-Length."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Track progress calls
        progress_calls = []

        def progress_callback(bytes_downloaded: int, total_bytes: int) -> None:
            progress_calls.append((bytes_downloaded, total_bytes))

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "16"}  # Two 8-byte chunks
            # Return chunks that sum to 16 bytes
            mock_response.iter_content.return_value = [b"chunk001", b"chunk002"]
            mock_get.return_value = mock_response

            download_file(
                "https://example.com/test.pdf", str(dest_path), progress_callback
            )

            assert dest_path.exists()

            # Verify progress was tracked correctly
            assert len(progress_calls) == 2
            assert progress_calls[0] == (
                8,
                16,
            )  # First chunk: 8 bytes downloaded, 16 total
            assert progress_calls[1] == (
                16,
                16,
            )  # Second chunk: 16 bytes downloaded, 16 total


def test_download_file_progress_callback_without_content_length() -> None:
    """Test progress callback when Content-Length header is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Track progress calls
        progress_calls = []

        def progress_callback(bytes_downloaded: int, total_bytes: int) -> None:
            progress_calls.append((bytes_downloaded, total_bytes))

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}  # No Content-Length header
            mock_response.iter_content.return_value = [b"data1", b"data2", b"data3"]
            mock_get.return_value = mock_response

            download_file(
                "https://example.com/test.pdf", str(dest_path), progress_callback
            )

            assert dest_path.exists()

            # Verify progress was tracked with -1 for unknown total
            assert len(progress_calls) == 3
            assert progress_calls[0] == (5, -1)  # 5 bytes downloaded, unknown total
            assert progress_calls[1] == (10, -1)  # 10 bytes downloaded, unknown total
            assert progress_calls[2] == (15, -1)  # 15 bytes downloaded, unknown total


def test_download_file_progress_callback_invalid_content_length() -> None:
    """Test progress callback when Content-Length header is invalid."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        # Track progress calls
        progress_calls = []

        def progress_callback(bytes_downloaded: int, total_bytes: int) -> None:
            progress_calls.append((bytes_downloaded, total_bytes))

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {
                "content-length": "not-a-number"
            }  # Invalid content length
            mock_response.iter_content.return_value = [b"testdata"]
            mock_get.return_value = mock_response

            download_file(
                "https://example.com/test.pdf", str(dest_path), progress_callback
            )

            assert dest_path.exists()

            # Verify progress was tracked with -1 for invalid total
            assert len(progress_calls) == 1
            assert progress_calls[0] == (
                8,
                -1,
            )  # 8 bytes downloaded, invalid total treated as unknown


def test_download_file_no_progress_callback() -> None:
    """Test that download works normally when no progress callback is provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "9"}  # Match "test data" size
            mock_response.iter_content.return_value = [b"test data"]
            mock_get.return_value = mock_response

            # Call without progress callback (None is the default)
            download_file("https://example.com/test.pdf", str(dest_path))

            assert dest_path.exists()
            with dest_path.open("rb") as f:
                assert f.read() == b"test data"


def test_download_file_progress_callback_error_handling() -> None:
    """Test that callback errors don't break the download."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "test.pdf"

        def failing_callback(_bytes_downloaded: int, _total_bytes: int) -> None:
            msg = "Callback failed!"
            raise RuntimeError(msg)

        with patch("paperorganize.download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "9"}
            mock_response.iter_content.return_value = [b"test data"]
            mock_get.return_value = mock_response

            # The download should succeed despite callback failure
            # Callback errors should not break the download
            download_file(
                "https://example.com/test.pdf", str(dest_path), failing_callback
            )

            assert dest_path.exists()
            # Verify file content was still written correctly
            assert dest_path.read_bytes() == b"test data"


def test_calculate_retry_delay_default_values() -> None:
    """Test retry delay calculation with default configuration."""
    # First retry (attempt 0): 1.0 * (2.0 ** 0) = 1.0
    assert calculate_retry_delay(0) == 1.0

    # Second retry (attempt 1): 1.0 * (2.0 ** 1) = 2.0
    assert calculate_retry_delay(1) == 2.0

    # Third retry (attempt 2): 1.0 * (2.0 ** 2) = 4.0
    assert calculate_retry_delay(2) == 4.0


def test_calculate_retry_delay_custom_values() -> None:
    """Test retry delay calculation with custom initial delay and multiplier."""
    # Custom initial delay of 0.5 seconds, multiplier of 3.0
    # First retry: 0.5 * (3.0 ** 0) = 0.5
    assert calculate_retry_delay(0, initial_delay=0.5, multiplier=3.0) == 0.5

    # Second retry: 0.5 * (3.0 ** 1) = 1.5
    assert calculate_retry_delay(1, initial_delay=0.5, multiplier=3.0) == 1.5

    # Third retry: 0.5 * (3.0 ** 2) = 4.5
    assert calculate_retry_delay(2, initial_delay=0.5, multiplier=3.0) == 4.5


def test_with_retry_successful_execution_after_retries() -> None:
    """Test that with_retry eventually succeeds after some failures."""

    call_count = 0

    def flaky_function() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < MAX_RETRY_ATTEMPTS:  # Fail first 2 attempts
            timeout_msg = TIMEOUT_MSG
            raise requests.exceptions.Timeout(timeout_msg)
        return "success"

    # Should succeed on the 3rd attempt (after 2 retries)
    result = with_retry(
        flaky_function,
        max_retries=3,
        retryable_exceptions=(requests.exceptions.Timeout,),
    )

    assert result == "success"
    assert call_count == MAX_RETRY_ATTEMPTS


def test_with_retry_exhausted_retries_scenario() -> None:
    """Test that with_retry raises the final exception when all retries are exhausted."""

    call_count = 0

    def always_failing_function() -> str:
        nonlocal call_count
        call_count += 1
        always_fails_msg = ALWAYS_FAILS_MSG
        raise requests.exceptions.Timeout(always_fails_msg)

    # Should exhaust all 2 retries and raise the final exception
    with pytest.raises(requests.exceptions.Timeout) as exc_info:
        with_retry(
            always_failing_function,
            max_retries=2,
            retryable_exceptions=(requests.exceptions.Timeout,),
        )

    assert ALWAYS_FAILS_MSG in str(exc_info.value)
    assert (
        call_count == MAX_RETRY_ATTEMPTS
    )  # Initial attempt + 2 retries = 3 total calls


def test_with_retry_non_retryable_exception_handling() -> None:
    """Test that with_retry immediately re-raises exceptions not in the retryable list."""

    call_count = 0

    def function_with_non_retryable_error() -> str:
        nonlocal call_count
        call_count += 1
        no_retry_msg = NO_RETRY_MSG
        raise ValueError(no_retry_msg)

    # ValueError is not in retryable_exceptions, should be raised immediately
    with pytest.raises(ValueError) as exc_info:
        with_retry(
            function_with_non_retryable_error,
            max_retries=3,
            retryable_exceptions=(requests.exceptions.Timeout,),
        )

    assert NO_RETRY_MSG in str(exc_info.value)
    assert call_count == 1  # Should only be called once, no retries


def test_with_retry_proper_delay_calculation_integration() -> None:
    """Test that with_retry correctly calls calculate_retry_delay() for each retry."""

    call_count = 0

    def failing_function() -> str:
        nonlocal call_count
        call_count += 1
        always_fails_msg = ALWAYS_FAILS_MSG
        raise requests.exceptions.Timeout(always_fails_msg)

    # Mock time.sleep to capture delay calculations
    with patch("paperorganize.download.time.sleep") as mock_sleep:
        with pytest.raises(requests.exceptions.Timeout):
            with_retry(
                failing_function,
                max_retries=2,
                retryable_exceptions=(requests.exceptions.Timeout,),
            )

        # Should have called sleep twice (for 2 retries)
        assert mock_sleep.call_count == RETRY_ATTEMPTS_MINUS_ONE

        # Verify the delay values match calculate_retry_delay expectations
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == INITIAL_DELAY  # First retry: 1.0 * (2.0 ** 0) = 1.0
        assert sleep_calls[1] == SECOND_DELAY  # Second retry: 1.0 * (2.0 ** 1) = 2.0


def test_with_retry_zero_retries() -> None:
    """Test with_retry behavior with zero retries (should fail immediately)."""

    call_count = 0

    def failing_function() -> str:
        nonlocal call_count
        call_count += 1
        immediate_failure_msg = IMMEDIATE_FAILURE_MSG
        raise requests.exceptions.Timeout(immediate_failure_msg)

    # With 0 retries, should fail on first attempt
    with pytest.raises(requests.exceptions.Timeout):
        with_retry(
            failing_function,
            max_retries=0,
            retryable_exceptions=(requests.exceptions.Timeout,),
        )

    assert call_count == 1  # Only initial attempt, no retries


def test_with_retry_empty_exception_tuple() -> None:
    """Test with_retry with empty retryable_exceptions tuple."""

    call_count = 0

    def failing_function() -> str:
        nonlocal call_count
        call_count += 1
        no_retry_expected_msg = NO_RETRY_EXPECTED_MSG
        raise requests.exceptions.Timeout(no_retry_expected_msg)

    # Empty exception tuple means nothing is retryable
    with pytest.raises(requests.exceptions.Timeout):
        with_retry(failing_function, max_retries=3, retryable_exceptions=())

    assert call_count == 1  # Should not retry when exception tuple is empty


def test_with_retry_successful_first_attempt() -> None:
    """Test with_retry when function succeeds on first attempt (no retries needed)."""

    call_count = 0

    def successful_function() -> str:
        nonlocal call_count
        call_count += 1
        return "immediate success"

    result = with_retry(
        successful_function,
        max_retries=3,
        retryable_exceptions=(requests.exceptions.Timeout,),
    )

    assert result == "immediate success"
    assert call_count == 1  # Should only be called once


def test_with_retry_multiple_retryable_exceptions() -> None:
    """Test with_retry with multiple exception types in retryable_exceptions."""

    call_count = 0

    def function_with_multiple_errors() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == FIRST_ATTEMPT:
            first_failure_msg = FIRST_FAILURE_MSG
            raise requests.exceptions.Timeout(first_failure_msg)
        if call_count == RETRY_ATTEMPTS_MINUS_ONE:
            second_failure_msg = SECOND_FAILURE_MSG
            raise requests.exceptions.ConnectionError(second_failure_msg)
        return "success after multiple error types"

    # Both Timeout and ConnectionError should be retryable
    result = with_retry(
        function_with_multiple_errors,
        max_retries=3,
        retryable_exceptions=(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ),
    )

    assert result == "success after multiple error types"
    assert call_count == MAX_RETRY_ATTEMPTS


def test_download_file_with_retry_integration() -> None:
    """Test that download_file integrates retry logic for network failures."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "retry_test.bin"
        call_count = 0

        def mock_requests_get(url: str, timeout: int | None = None) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < MAX_RETRY_ATTEMPTS:
                # First 2 attempts fail with network timeout
                timeout_msg = TIMEOUT_MSG
                raise requests.exceptions.Timeout(timeout_msg)
            # Third attempt succeeds
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "4"}
            mock_response.iter_content.return_value = [b"test"]
            return mock_response

        with patch(
            "paperorganize.download.requests.get", side_effect=mock_requests_get
        ):
            # Should succeed after retries
            download_file("https://example.com/test.pdf", str(dest_path))

        # Verify file was created and has correct content
        assert dest_path.exists()
        assert dest_path.read_bytes() == b"test"

        # Verify retry logic was used (3 attempts total)
        assert call_count == MAX_RETRY_ATTEMPTS


def test_download_file_retry_respects_http_errors() -> None:
    """Test that download_file does NOT retry HTTP errors (only network errors)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_path = Path(temp_dir) / "http_error_test.bin"
        call_count = 0

        def mock_requests_get(url: str, timeout: int | None = None) -> MagicMock:
            nonlocal call_count
            call_count += 1
            # Return 404 HTTP error immediately
            mock_response = MagicMock()
            mock_response.status_code = HTTP_NOT_FOUND
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "404 Not Found"
            )
            return mock_response

        with patch(
            "paperorganize.download.requests.get", side_effect=mock_requests_get
        ), pytest.raises(HTTPError):
            # HTTP errors should NOT be retried
            download_file("https://example.com/missing.pdf", str(dest_path))

        # Should only be called once (no retries for HTTP errors)
        assert call_count == FIRST_ATTEMPT


class TestHeaderProcessing:
    """Test header processing functionality."""

    def test_is_pdf_content_type_valid_pdf(self) -> None:
        """Test PDF content type detection with valid PDF type."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}

        assert _is_pdf_content_type(mock_response) is True

    def test_is_pdf_content_type_pdf_with_charset(self) -> None:
        """Test PDF content type detection with charset parameter."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf; charset=utf-8"}

        assert _is_pdf_content_type(mock_response) is True

    def test_is_pdf_content_type_case_insensitive(self) -> None:
        """Test PDF content type detection is case insensitive."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "APPLICATION/PDF"}

        assert _is_pdf_content_type(mock_response) is True

    def test_is_pdf_content_type_not_pdf(self) -> None:
        """Test PDF content type detection with non-PDF type."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}

        assert _is_pdf_content_type(mock_response) is False

    def test_is_pdf_content_type_missing_header(self) -> None:
        """Test PDF content type detection with missing header."""
        mock_response = MagicMock()
        mock_response.headers = {}

        assert _is_pdf_content_type(mock_response) is False

    def test_extract_filename_from_content_disposition_quoted(self) -> None:
        """Test filename extraction from quoted Content-Disposition header."""
        mock_response = MagicMock()
        mock_response.headers = {
            "content-disposition": 'attachment; filename="document.pdf"'
        }

        result = _extract_filename_from_content_disposition(mock_response)
        assert result == "document.pdf"

    def test_extract_filename_from_content_disposition_inline(self) -> None:
        """Test filename extraction from inline Content-Disposition header."""
        mock_response = MagicMock()
        mock_response.headers = {
            "content-disposition": 'inline; filename="1901.06032v7.pdf"'
        }

        result = _extract_filename_from_content_disposition(mock_response)
        assert result == "1901.06032v7.pdf"

    def test_extract_filename_from_content_disposition_unquoted(self) -> None:
        """Test filename extraction from unquoted Content-Disposition header."""
        mock_response = MagicMock()
        mock_response.headers = {
            "content-disposition": "attachment; filename=simple.pdf"
        }

        result = _extract_filename_from_content_disposition(mock_response)
        assert result == "simple.pdf"

    def test_extract_filename_from_content_disposition_single_quotes(self) -> None:
        """Test filename extraction with single quotes."""
        mock_response = MagicMock()
        mock_response.headers = {
            "content-disposition": "attachment; filename='quoted.pdf'"
        }

        result = _extract_filename_from_content_disposition(mock_response)
        assert result == "quoted.pdf"

    def test_extract_filename_from_content_disposition_missing_header(self) -> None:
        """Test filename extraction with missing Content-Disposition header."""
        mock_response = MagicMock()
        mock_response.headers = {}

        result = _extract_filename_from_content_disposition(mock_response)
        assert result is None

    def test_extract_filename_from_content_disposition_no_filename(self) -> None:
        """Test filename extraction with Content-Disposition but no filename."""
        mock_response = MagicMock()
        mock_response.headers = {"content-disposition": "attachment"}

        result = _extract_filename_from_content_disposition(mock_response)
        assert result is None


class TestGetDownloadInfo:
    """Test get_download_info functionality."""

    def test_get_download_info_pdf_with_filename(self) -> None:
        """Test getting download info for PDF with filename in headers."""
        with patch("paperorganize.download.requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.headers = {
                "content-type": "application/pdf",
                "content-disposition": 'inline; filename="paper.pdf"',
            }
            mock_head.return_value = mock_response

            suggested_filename, is_pdf_content = get_download_info(
                "https://example.com/paper"
            )

            assert suggested_filename == "paper.pdf"
            assert is_pdf_content is True

    def test_get_download_info_pdf_no_filename(self) -> None:
        """Test getting download info for PDF without filename in headers."""
        with patch("paperorganize.download.requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "application/pdf"}
            mock_head.return_value = mock_response

            suggested_filename, is_pdf_content = get_download_info(
                "https://example.com/paper"
            )

            assert suggested_filename is None
            assert is_pdf_content is True

    def test_get_download_info_not_pdf(self) -> None:
        """Test getting download info for non-PDF content."""
        with patch("paperorganize.download.requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.headers = {
                "content-type": "text/html",
                "content-disposition": 'inline; filename="page.html"',
            }
            mock_head.return_value = mock_response

            suggested_filename, is_pdf_content = get_download_info(
                "https://example.com/page"
            )

            assert suggested_filename == "page.html"
            assert is_pdf_content is False
