# ABOUTME: HTTP download functionality with progress bars and retry logic
# ABOUTME: Handles fetching PDFs from URLs with network error handling
# SPDX-License-Identifier: MIT

import contextlib
import re
import time
from pathlib import Path
from typing import Callable, Optional, TypeVar
from urllib.parse import urlparse

import requests

from .exceptions import FileSystemError, HTTPError, NetworkError, ValidationError

# Retry configuration constants
MAX_NETWORK_RETRIES = 3  # Network timeouts and connection errors
INITIAL_RETRY_DELAY = 1.0  # Initial delay in seconds
BACKOFF_MULTIPLIER = 2.0  # Exponential backoff multiplier


def calculate_retry_delay(
    attempt: int,
    initial_delay: float = INITIAL_RETRY_DELAY,
    multiplier: float = BACKOFF_MULTIPLIER,
) -> float:
    """Calculate exponential backoff delay for retry attempts.

    Args:
        attempt: Current retry attempt number (0-based)
        initial_delay: Base delay in seconds
        multiplier: Exponential growth factor

    Returns:
        Calculated delay in seconds for this attempt

    Examples:
        >>> calculate_retry_delay(0)  # First retry
        1.0
        >>> calculate_retry_delay(1)  # Second retry
        2.0
        >>> calculate_retry_delay(2)  # Third retry
        4.0
    """
    return initial_delay * (multiplier**attempt)


# Type variable for generic retry function
T = TypeVar("T")


def with_retry(
    func: Callable[[], T],
    max_retries: int,
    retryable_exceptions: tuple[type[Exception], ...],
    initial_delay: float = INITIAL_RETRY_DELAY,
    multiplier: float = BACKOFF_MULTIPLIER,
) -> T:
    """Execute function with exponential backoff retry logic.

    Args:
        func: Function to execute (takes no arguments)
        max_retries: Maximum number of retry attempts
        retryable_exceptions: Exception types that trigger retries
        initial_delay: Base delay in seconds for first retry
        multiplier: Exponential backoff multiplier

    Returns:
        Result of successful function execution

    Raises:
        The final exception if all retries are exhausted
        Any non-retryable exception immediately

    Examples:
        >>> def failing_request():
        ...     response = requests.get("http://example.com")
        ...     response.raise_for_status()
        ...     return response
        >>> result = with_retry(
        ...     failing_request,
        ...     max_retries=3,
        ...     retryable_exceptions=(requests.exceptions.Timeout,)
        ... )
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as e:  # noqa: PERF203
            last_exception = e
            if attempt < max_retries:
                delay = calculate_retry_delay(attempt, initial_delay, multiplier)
                time.sleep(delay)
            # If this was the last attempt, we'll raise below
        except Exception:
            # Non-retryable exception - raise immediately
            raise

    # All retries exhausted - raise the last exception
    if last_exception is not None:
        raise last_exception

    # This should never happen, but for type checker completeness
    error_msg = "Retry logic failed unexpectedly"
    raise RuntimeError(error_msg)


def _validate_download_inputs(url: str, destination_path: str) -> None:
    """Validate download function inputs.

    Args:
        url: Source URL to download from
        destination_path: Local file path to save to

    Raises:
        ValidationError: If inputs are invalid
    """
    if not url or not isinstance(url, str):
        msg = "URL must be a non-empty string"
        raise ValidationError(msg, field="url", value=url)

    if not destination_path or not isinstance(destination_path, str):
        msg = "Destination path must be a non-empty string"
        raise ValidationError(
            msg,
            field="destination_path",
            value=destination_path,
        )

    # Basic URL validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        msg = "URL must have a valid scheme and hostname"
        raise ValidationError(msg, field="url", value=url)

    if parsed.scheme not in ("http", "https"):
        msg = "URL must use HTTP or HTTPS protocol"
        raise ValidationError(msg, field="url", value=url)


def _prepare_destination(destination_path: str) -> Path:
    """Prepare destination directory for file download.

    Args:
        destination_path: Local file path to save to

    Returns:
        Path object for the destination

    Raises:
        FileSystemError: If directory creation fails
    """
    dest_path = Path(destination_path)
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        msg = f"Cannot create parent directory: {e}"
        raise FileSystemError(msg, path=str(dest_path.parent)) from e
    return dest_path


def _fetch_response(url: str) -> requests.Response:
    """Fetch HTTP response with error handling.

    Args:
        url: Source URL to download from

    Returns:
        HTTP response object

    Raises:
        NetworkError: If network request fails
        HTTPError: If HTTP response indicates an error
    """
    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.Timeout as e:
        msg = "Request timed out after 30 seconds"
        raise NetworkError(msg, details={"url": url}) from e
    except requests.exceptions.ConnectionError as e:
        msg = f"Connection failed: {e}"
        raise NetworkError(msg, details={"url": url}) from e
    except requests.exceptions.RequestException as e:
        msg = f"Request failed: {e}"
        raise NetworkError(msg, details={"url": url}) from e

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        msg = f"HTTP request failed: {e}"
        raise HTTPError(msg, status_code=response.status_code, url=url) from e

    return response


def _is_pdf_content_type(response: requests.Response) -> bool:
    """Check if response Content-Type indicates a PDF.

    Args:
        response: HTTP response object

    Returns:
        True if Content-Type indicates PDF, False otherwise
    """
    content_type = response.headers.get("content-type", "").lower()
    return content_type.startswith("application/pdf")


def _extract_filename_from_content_disposition(
    response: requests.Response,
) -> Optional[str]:
    """Extract filename from Content-Disposition header.

    Args:
        response: HTTP response object

    Returns:
        Extracted filename if found, None otherwise

    Examples:
        >>> # For header: 'attachment; filename="document.pdf"'
        >>> _extract_filename_from_content_disposition(response)
        'document.pdf'
        >>> # For header: 'inline; filename="1901.06032v7.pdf"'
        >>> _extract_filename_from_content_disposition(response)
        '1901.06032v7.pdf'
    """
    content_disposition = response.headers.get("content-disposition", "")
    if not content_disposition:
        return None

    # Look for filename= or filename*= patterns
    # Handle both quoted and unquoted filenames
    patterns = [
        r'filename\*?=\s*"([^"]+)"',  # filename="file.pdf" or filename*="file.pdf"
        r"filename\*?=\s*'([^']+)'",  # filename='file.pdf'
        r"filename\*?=\s*([^;,\s]+)",  # filename=file.pdf (unquoted)
    ]

    for pattern in patterns:
        match = re.search(pattern, content_disposition, re.IGNORECASE)
        if match:
            filename = match.group(1).strip()
            # Handle RFC 5987 encoded filenames (UTF-8'en'filename)
            if "*=" in content_disposition.lower() and "'" in filename:
                # Simple handling of UTF-8'lang'filename format
                filename = filename.split("'")[-1]
            return filename

    return None


def _get_content_length(response: requests.Response) -> int:
    """Extract content length from response headers.

    Args:
        response: HTTP response object

    Returns:
        Content length in bytes, or -1 if unknown
    """
    if "content-length" in response.headers:
        try:
            return int(response.headers["content-length"])
        except (ValueError, TypeError):
            pass
    return -1


def _write_content_to_file(
    response: requests.Response,
    dest_path: Path,
    progress_callback: Optional[Callable[[int, int], None]],
    total_bytes: int,
) -> int:
    """Write response content to file with progress tracking.

    Args:
        response: HTTP response object
        dest_path: Destination file path
        progress_callback: Optional progress callback
        total_bytes: Total content length (-1 if unknown)

    Returns:
        Number of bytes successfully downloaded

    Raises:
        FileSystemError: If file operations fail
    """
    bytes_downloaded = 0
    try:
        with dest_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    try:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                    except OSError as e:
                        msg = f"Failed to write to file: {e}"
                        raise FileSystemError(msg, path=str(dest_path)) from e

                    # Call progress callback if provided
                    if progress_callback:
                        with contextlib.suppress(Exception):
                            progress_callback(bytes_downloaded, total_bytes)

    except OSError as e:
        # Clean up partial file on any file system error
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        msg = f"File operation failed: {e}"
        raise FileSystemError(msg, path=str(dest_path)) from e

    except Exception:
        # Clean up partial file on any other error
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        raise

    return bytes_downloaded


def _fetch_response_with_retry(url: str) -> requests.Response:
    """Fetch HTTP response with retry logic for network failures.

    Args:
        url: Source URL to download from

    Returns:
        HTTP response object

    Raises:
        NetworkError: If network request fails after all retries
        HTTPError: If HTTP response indicates an error (no retry)
    """

    def make_request() -> requests.Response:
        return requests.get(url, timeout=30)

    try:
        response = with_retry(
            make_request,
            max_retries=MAX_NETWORK_RETRIES,
            retryable_exceptions=(
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ),
            initial_delay=INITIAL_RETRY_DELAY,
            multiplier=BACKOFF_MULTIPLIER,
        )
    except (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
    ) as e:
        # Convert to domain exception
        if isinstance(e, requests.exceptions.Timeout):
            msg = "Request timed out after 30 seconds"
        else:
            msg = f"Connection failed: {e}"
        raise NetworkError(msg, details={"url": url}) from e
    except requests.exceptions.RequestException as e:
        msg = f"Request failed: {e}"
        raise NetworkError(msg, details={"url": url}) from e

    # Handle HTTP status errors (no retry)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        msg = f"HTTP request failed: {e}"
        raise HTTPError(msg, status_code=response.status_code, url=url) from e

    return response


def get_download_info(url: str) -> tuple[Optional[str], bool]:
    """Get download information from URL headers without downloading content.

    Args:
        url: URL to check

    Returns:
        Tuple of (suggested_filename, is_pdf_content)
        - suggested_filename: Filename from Content-Disposition or None
        - is_pdf_content: True if Content-Type indicates PDF

    Raises:
        ValidationError: If input parameters are invalid
        NetworkError: If network request fails
        HTTPError: If HTTP response indicates an error
    """
    # Input validation
    if not url or not isinstance(url, str):
        msg = "URL must be a non-empty string"
        raise ValidationError(msg, field="url", value=url)

    # Basic URL validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        msg = "URL must have a valid scheme and hostname"
        raise ValidationError(msg, field="url", value=url)

    if parsed.scheme not in ("http", "https"):
        msg = "URL must use HTTP or HTTPS protocol"
        raise ValidationError(msg, field="url", value=url)

    # Make HEAD request to get headers
    try:
        response = requests.head(url, timeout=30, allow_redirects=True)
    except requests.exceptions.Timeout as e:
        msg = "Request timed out after 30 seconds"
        raise NetworkError(msg, details={"url": url}) from e
    except requests.exceptions.ConnectionError as e:
        msg = f"Connection failed: {e}"
        raise NetworkError(msg, details={"url": url}) from e
    except requests.exceptions.RequestException as e:
        msg = f"Request failed: {e}"
        raise NetworkError(msg, details={"url": url}) from e

    # Handle HTTP status errors
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        msg = f"HTTP request failed: {e}"
        raise HTTPError(msg, status_code=response.status_code, url=url) from e

    # Extract information from headers
    suggested_filename = _extract_filename_from_content_disposition(response)
    is_pdf_content = _is_pdf_content_type(response)

    return suggested_filename, is_pdf_content


def download_file(
    url: str,
    destination_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    """Download a file from URL to destination path.

    Args:
        url: Source URL to download from
        destination_path: Local file path to save to
        progress_callback: Optional callback for progress tracking.
                          Called with (bytes_downloaded, total_bytes).
                          total_bytes is -1 if Content-Length is unknown.

    Raises:
        ValidationError: If input parameters are invalid
        NetworkError: If network request fails
        HTTPError: If HTTP response indicates an error
        FileSystemError: If file operations fail
    """
    # Input validation
    _validate_download_inputs(url, destination_path)

    # Prepare destination directory
    dest_path = _prepare_destination(destination_path)

    # Fetch HTTP response with retry logic for network failures
    response = _fetch_response_with_retry(url)

    # Get content length
    total_bytes = _get_content_length(response)

    # Write content to file
    bytes_downloaded = _write_content_to_file(
        response, dest_path, progress_callback, total_bytes
    )

    # Content validation if size is known
    if total_bytes > 0 and bytes_downloaded != total_bytes:
        # Clean up incomplete file
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        msg = f"Download incomplete: expected {total_bytes} bytes, got {bytes_downloaded} bytes"
        raise ValidationError(
            msg,
            details={"expected_bytes": total_bytes, "actual_bytes": bytes_downloaded},
        )
