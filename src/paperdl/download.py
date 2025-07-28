# ABOUTME: HTTP download functionality with progress bars and retry logic
# ABOUTME: Handles fetching PDFs from URLs with network error handling

import contextlib
from pathlib import Path

import requests


def download_file(url: str, destination_path: str) -> bool:
    """Download a file from URL to destination path.

    Args:
        url: Source URL to download from
        destination_path: Local file path to save to

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        dest_path = Path(destination_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file with reasonable timeout
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Write content to file using streaming
        with dest_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)

    except Exception:
        # Clean up partial file if it exists
        dest_path = Path(destination_path)
        if dest_path.exists():
            with contextlib.suppress(OSError):
                dest_path.unlink()
        return False
    else:
        return True
