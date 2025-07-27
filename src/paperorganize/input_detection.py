# ABOUTME: Input type detection and validation for paper-organize
# ABOUTME: Determines whether input is URL, file, or directory for unified processing
# SPDX-License-Identifier: MIT

from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

from .exceptions import ValidationError


class InputType(Enum):
    """Types of input that paper-organize can process."""

    URL = "url"
    FILE = "file"
    DIRECTORY = "directory"


def detect_input_type(input_arg: str) -> InputType:
    """Detect the type of input argument.

    Args:
        input_arg: The input string to analyze

    Returns:
        InputType: The detected type of input

    Raises:
        ValidationError: If input type cannot be determined or is invalid
    """
    # Check if it's a URL
    if input_arg.startswith(("http://", "https://")):
        parsed = urlparse(input_arg)
        if not parsed.netloc:
            raise ValidationError(
                f"Invalid URL: {input_arg}",
                details={
                    "input": input_arg,
                    "suggestion": "Ensure URL includes protocol (http:// or https://)",
                },
            )
        return InputType.URL

    # Check if it's a local path
    path = Path(input_arg)

    if path.is_file():
        if not path.suffix.lower() == ".pdf":
            raise ValidationError(
                f"File must be a PDF: {input_arg}",
                details={
                    "input": input_arg,
                    "file_type": path.suffix or "no extension",
                    "suggestion": "Only PDF files are supported",
                },
            )
        return InputType.FILE

    if path.is_dir():
        return InputType.DIRECTORY

    # If we get here, it's neither a valid URL nor an existing file/directory
    raise ValidationError(
        f"Invalid input: {input_arg}",
        details={
            "input": input_arg,
            "suggestion": "Provide a valid URL, PDF file path, or directory path",
        },
    )


def validate_directory_contains_pdfs(directory: Path) -> list[Path]:
    """Validate that a directory contains PDF files and return them.

    Args:
        directory: Path to directory to check

    Returns:
        List of PDF file paths found in directory

    Raises:
        ValidationError: If directory contains no PDF files
    """
    pdf_files = list(directory.glob("*.pdf"))

    if not pdf_files:
        raise ValidationError(
            f"No PDF files found in directory: {directory}",
            details={
                "directory": str(directory),
                "suggestion": "Ensure directory contains PDF files",
            },
        )

    return sorted(pdf_files)
