# ABOUTME: Shared metadata naming utilities for intelligent PDF organization
# ABOUTME: Provides common metadata extraction and filename generation functionality
# SPDX-License-Identifier: MIT

from pathlib import Path

import click

from .metadata import extract_pdf_metadata, generate_filename


def apply_metadata_naming(file_path: Path, *, quiet: bool) -> Path:
    """Apply metadata-based naming to a PDF file.

    Extracts metadata from the PDF and renames it with an intelligent filename.
    Handles conflicts by appending numbers and gracefully falls back on errors.

    Args:
        file_path: Path to the PDF file to rename
        quiet: Whether to suppress output messages

    Returns:
        Path to the final file (may be same as input if no rename needed)
    """
    try:
        # Extract metadata
        metadata = extract_pdf_metadata(str(file_path))
        new_filename = generate_filename(metadata, file_path.name)

        # If no change needed, return original
        if new_filename == file_path.name:
            return file_path

        # Handle conflicts
        new_path = file_path.parent / new_filename
        counter = 1
        original_new_path = new_path
        while new_path.exists():
            stem = original_new_path.stem
            suffix = original_new_path.suffix
            new_path = file_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        # Rename
        file_path.rename(new_path)

        if not quiet:
            click.echo(f"✓ Renamed to: {new_path.name}")

        return new_path

    except Exception as e:
        if not quiet:
            click.echo(f"⚠ Could not extract metadata: {e}", err=True)
        return file_path
