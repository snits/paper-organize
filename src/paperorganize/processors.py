# ABOUTME: Input processors for different sources (URL, file, directory)
# ABOUTME: Strategy pattern implementation for unified paper processing
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import click
import requests

from .download import download_file, get_download_info
from .exceptions import HTTPError, NetworkError, ValidationError
from .input_detection import validate_directory_contains_pdfs
from .metadata_naming import apply_metadata_naming


class ProcessingResult:
    """Result of processing a single PDF file."""

    def __init__(
        self,
        original_path: Path,
        final_path: Path,
        *,
        was_downloaded: bool = False,
        was_renamed: bool = False,
    ):
        self.original_path = original_path
        self.final_path = final_path
        self.was_downloaded = was_downloaded
        self.was_renamed = was_renamed


class InputProcessor(Protocol):
    """Protocol for processing different input types."""

    def process(
        self,
        input_arg: str,
        destination_dir: Path,
        custom_name: str | None,
        *,
        auto_name: bool,
        quiet: bool,
    ) -> list[ProcessingResult]:
        """Process the input and return results."""
        ...


class URLProcessor:
    """Processor for URL inputs - downloads and organizes."""

    def process(
        self,
        input_arg: str,
        destination_dir: Path,
        custom_name: str | None,
        *,
        auto_name: bool,
        quiet: bool,
    ) -> list[ProcessingResult]:
        """Download from URL and organize."""
        if not quiet:
            click.echo(f"→ Downloading from URL: {input_arg}")

        # Determine filename
        filename = self._determine_filename(custom_name, input_arg)
        temp_path = destination_dir / filename

        # Download file
        download_file(input_arg, str(temp_path))

        if not quiet:
            click.echo(f"✓ Downloaded to: {temp_path}")

        # Apply metadata naming if enabled
        final_path = temp_path
        was_renamed = False

        if auto_name and custom_name is None:
            final_path = apply_metadata_naming(temp_path, quiet=quiet)
            was_renamed = final_path != temp_path

        return [
            ProcessingResult(
                original_path=temp_path,
                final_path=final_path,
                was_downloaded=True,
                was_renamed=was_renamed,
            )
        ]

    def _determine_filename(self, custom_name: str | None, url: str) -> str:
        """Determine filename for download."""
        if custom_name is not None:
            filename = custom_name
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            return filename

        # Try to get filename from server headers first
        try:
            suggested_filename, is_pdf_content = get_download_info(url)

            # If server provides a filename and confirms it's a PDF, use it
            if suggested_filename and is_pdf_content:
                if not suggested_filename.endswith(".pdf"):
                    suggested_filename += ".pdf"
                return suggested_filename

            # If server confirms it's a PDF but no filename, extract from URL and add .pdf
            if is_pdf_content:
                parsed_url = urlparse(url)
                filename = Path(parsed_url.path).name
                if filename:
                    return (
                        filename + ".pdf" if not filename.endswith(".pdf") else filename
                    )

        except (ValidationError, NetworkError, HTTPError, requests.RequestException):
            # If header check fails, fall back to URL parsing
            # Header checking is optional - we should never fail filename determination
            # due to network issues, server errors, or unexpected response formats
            pass

        # Fallback: Extract from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = "paper.pdf"
        elif not filename.endswith(".pdf"):
            filename = filename + ".pdf"
        return filename


class FileProcessor:
    """Processor for single file inputs - organizes existing PDFs."""

    def process(
        self,
        input_arg: str,
        destination_dir: Path,
        custom_name: str | None,
        *,
        auto_name: bool,
        quiet: bool,
    ) -> list[ProcessingResult]:
        """Process existing PDF file."""
        source_path = Path(input_arg)

        if not quiet:
            click.echo(f"→ Processing existing file: {source_path}")

        # Determine destination
        if custom_name is not None:
            filename = custom_name
            if not filename.endswith(".pdf"):
                filename += ".pdf"
        else:
            filename = source_path.name

        destination_path = destination_dir / filename

        # Copy or move file to destination if different
        if source_path.parent != destination_dir or filename != source_path.name:
            # Handle conflicts
            counter = 1
            original_dest = destination_path
            while destination_path.exists() and destination_path != source_path:
                stem = original_dest.stem
                suffix = original_dest.suffix
                destination_path = destination_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            # Copy file to destination
            if destination_path != source_path:
                destination_path.write_bytes(source_path.read_bytes())
                if not quiet:
                    click.echo(f"✓ Copied to: {destination_path}")
        else:
            destination_path = source_path

        # Apply metadata naming if enabled
        final_path = destination_path
        was_renamed = False

        if auto_name and custom_name is None:
            final_path = apply_metadata_naming(destination_path, quiet=quiet)
            was_renamed = final_path != destination_path

        return [
            ProcessingResult(
                original_path=source_path,
                final_path=final_path,
                was_downloaded=False,
                was_renamed=was_renamed,
            )
        ]


class DirectoryProcessor:
    """Processor for directory inputs - batch organizes all PDFs."""

    def process(
        self,
        input_arg: str,
        destination_dir: Path,
        custom_name: str | None,  # noqa: ARG002
        *,
        auto_name: bool,
        quiet: bool,
    ) -> list[ProcessingResult]:
        """Process all PDF files in directory."""
        source_dir = Path(input_arg)

        # Find all PDF files
        pdf_files = validate_directory_contains_pdfs(source_dir)

        if not quiet:
            click.echo(f"→ Processing directory: {source_dir}")
            click.echo(f"Found {len(pdf_files)} PDF files")

        results = []
        file_processor = FileProcessor()

        for pdf_file in pdf_files:
            if not quiet:
                click.echo(f"\n  Processing: {pdf_file.name}")

            # Process each file individually
            # Note: custom_name is ignored for batch processing
            file_results = file_processor.process(
                str(pdf_file),
                destination_dir,
                custom_name=None,  # No custom names in batch mode
                auto_name=auto_name,
                quiet=quiet,
            )
            results.extend(file_results)

        if not quiet:
            click.echo(f"\n✓ Processed {len(results)} files")

        return results
