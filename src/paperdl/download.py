# ABOUTME: HTTP download functionality with progress bars and retry logic
# ABOUTME: Handles fetching PDFs from URLs with network error handling

import contextlib
import time
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import requests

from .exceptions import FileSystemError, HTTPError, NetworkError, ValidationError

# Retry configuration constants
MAX_NETWORK_RETRIES = 3  # Network timeouts and connection errors
MAX_SERVER_ERROR_RETRIES = 2  # HTTP 5xx server errors  
INITIAL_RETRY_DELAY = 1.0  # Initial delay in seconds
BACKOFF_MULTIPLIER = 2.0  # Exponential backoff multiplier


def calculate_retry_delay(attempt: int, initial_delay: float = INITIAL_RETRY_DELAY, 
                         multiplier: float = BACKOFF_MULTIPLIER) -> float:
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
    return initial_delay * (multiplier ** attempt)


def _validate_download_inputs(url: str, destination_path: str) -> None:
    """Validate download function inputs.
    
    Args:
        url: Source URL to download from
        destination_path: Local file path to save to
        
    Raises:
        ValidationError: If inputs are invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string", field="url", value=url)

    if not destination_path or not isinstance(destination_path, str):
        raise ValidationError("Destination path must be a non-empty string",
                            field="destination_path", value=destination_path)

    # Basic URL validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValidationError("URL must have a valid scheme and hostname",
                            field="url", value=url)

    if parsed.scheme not in ("http", "https"):
        raise ValidationError("URL must use HTTP or HTTPS protocol",
                            field="url", value=url)


def download_file(
    url: str,
    destination_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
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

    dest_path = Path(destination_path)

    # Create parent directory if it doesn't exist
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise FileSystemError(
            f"Cannot create parent directory: {e}",
            path=str(dest_path.parent)
        ) from e
    # Download file with network error handling
    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.Timeout as e:
        raise NetworkError("Request timed out after 30 seconds",
                         details={"url": url}) from e
    except requests.exceptions.ConnectionError as e:
        raise NetworkError(f"Connection failed: {e}",
                         details={"url": url}) from e
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Request failed: {e}",
                         details={"url": url}) from e

    # Handle HTTP errors
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise HTTPError(
            f"HTTP request failed: {e}",
            status_code=response.status_code,
            url=url
        ) from e

    # Extract total size from Content-Length header
    total_bytes = -1
    if "content-length" in response.headers:
        try:
            total_bytes = int(response.headers["content-length"])
        except (ValueError, TypeError):
            total_bytes = -1

    # Write content to file with proper error handling and cleanup
    bytes_downloaded = 0
    try:
        with dest_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    try:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                    except OSError as e:
                        raise FileSystemError(
                            f"Failed to write to file: {e}",
                            path=str(dest_path)
                        ) from e

                    # Call progress callback if provided
                    if progress_callback:
                        with contextlib.suppress(Exception):
                            progress_callback(bytes_downloaded, total_bytes)

    except OSError as e:
        # Clean up partial file on any file system error
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        raise FileSystemError(
            f"File operation failed: {e}",
            path=str(dest_path)
        ) from e

    except Exception:
        # Clean up partial file on any other error
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        raise

    # Content validation if size is known
    if total_bytes > 0 and bytes_downloaded != total_bytes:
        # Clean up incomplete file
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        raise ValidationError(
            f"Download incomplete: expected {total_bytes} bytes, got {bytes_downloaded} bytes",
            details={"expected_bytes": total_bytes, "actual_bytes": bytes_downloaded}
        )
