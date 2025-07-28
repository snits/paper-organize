# ABOUTME: Command-line interface for paper-organize with Click framework
# ABOUTME: Handles unified input processing (URLs, files, directories) with intelligent organization
# SPDX-License-Identifier: MIT

import os
from pathlib import Path

import click

from .exceptions import (
    FileSystemError,
    HTTPError,
    NetworkError,
    PaperDLError,
    ValidationError,
)
from .input_detection import InputType, detect_input_type
from .processors import DirectoryProcessor, FileProcessor, URLProcessor


def _determine_download_directory(directory: str | None) -> Path:
    """Determine download directory following UX hierarchy: --dir > PAPERS_DIR > ~/Papers > cwd.

    Note: Does not create directories, just determines the path.
    """
    if directory is not None:
        # 1. Command line --dir flag (highest priority)
        return Path(directory).expanduser()

    if papers_dir := os.environ.get("PAPERS_DIR"):
        # 2. PAPERS_DIR environment variable
        return Path(papers_dir).expanduser()

    # 3. Default: ~/Papers (will be created by _setup_download_directory)
    return Path.home() / "Papers"


def _setup_download_directory(
    directory: str | None, *, quiet: bool = False
) -> tuple[Path, bool]:
    """Set up and return the download directory with first-run messaging.

    Returns:
        Tuple of (directory_path, is_first_run_papers_dir)
    """
    # Check first-run condition BEFORE calling _determine_download_directory
    papers_dir = Path.home() / "Papers"
    is_first_run = (
        directory is None
        and os.environ.get("PAPERS_DIR") is None
        and not papers_dir.exists()
    )

    # Now determine directory (but not create yet)
    download_dir = _determine_download_directory(directory)

    # Create directory with fallback logic
    try:
        download_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        # If we were trying to create ~/Papers and failed, fallback to current directory
        if (
            download_dir == papers_dir
            and directory is None
            and os.environ.get("PAPERS_DIR") is None
        ):
            download_dir = Path.cwd()
            is_first_run = False  # Not first run if we fallback
            try:
                download_dir.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as fallback_e:
                suggested_fix = (
                    "Set PAPERS_DIR or use --dir to specify a writable location"
                )
                error_message = f"Cannot create directory '{download_dir}'"
                raise FileSystemError(
                    error_message,
                    details={
                        "directory": str(download_dir),
                        "error": str(fallback_e),
                        "suggestion": suggested_fix,
                    },
                ) from fallback_e
        else:
            # For custom directories, fail with helpful message
            suggested_fix = "Set PAPERS_DIR or use --dir to specify a writable location"
            error_message = f"Cannot create directory '{download_dir}'"
            raise FileSystemError(
                error_message,
                details={
                    "directory": str(download_dir),
                    "error": str(e),
                    "suggestion": suggested_fix,
                },
            ) from e

    # Show first-run message for ~/Papers creation
    if is_first_run and not quiet:
        click.echo(
            f"📁 Created {papers_dir} directory for your organized papers", err=True
        )
        click.echo(
            "   Use --dir to specify a different location, or set PAPERS_DIR", err=True
        )

    return download_dir, is_first_run


# Note: Helper functions for filename determination and metadata processing
# have been moved to the processor classes for better organization


def _handle_error(e: Exception, *, quiet: bool) -> None:  # noqa: ARG001
    """Handle and report errors consistently."""
    if hasattr(e, "user_message"):
        click.echo(f"✗ {e.user_message()}", err=True)
    else:
        click.echo(f"✗ Unexpected error: {e}", err=True)
    raise click.Abort from e


@click.command()
@click.argument("input_arg", metavar="INPUT")
@click.option(
    "--dir",
    "directory",
    help="Directory to save organized files (overrides PAPERS_DIR)",
)
@click.option("--name", help="Custom filename for the organized file")
@click.option(
    "--no-auto-name",
    is_flag=True,
    help="Disable automatic filename generation from PDF metadata",
)
@click.option("--quiet", is_flag=True, help="Suppress output for scripting")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def main(
    input_arg: str,
    directory: str | None,
    name: str | None,
    *,
    no_auto_name: bool,
    quiet: bool,
    verbose: bool,
) -> None:
    """Organize academic papers with intelligent metadata extraction and descriptive filenames.

    INPUT can be:
      • URL          Download and organize a paper from the web
      • PDF file     Organize an existing PDF file
      • Directory    Batch organize all PDFs in a directory

    Directory Priority: --dir > PAPERS_DIR environment variable > ~/Papers (default)
    """
    del verbose  # Currently unused, but reserved for future features

    try:
        # Detect input type
        input_type = detect_input_type(input_arg)

        # Set up destination directory
        destination_dir, is_first_run = _setup_download_directory(
            directory, quiet=quiet
        )

        # Select appropriate processor
        processor: URLProcessor | FileProcessor | DirectoryProcessor
        if input_type == InputType.URL:
            processor = URLProcessor()
        elif input_type == InputType.FILE:
            processor = FileProcessor()
        else:  # InputType.DIRECTORY
            processor = DirectoryProcessor()

        # Process input
        results = processor.process(
            input_arg,
            destination_dir,
            name,
            auto_name=not no_auto_name,
            quiet=quiet,
        )

        # Show summary if not quiet
        if not quiet and len(results) > 1:
            click.echo(f"\n📊 Summary: Processed {len(results)} files")

    except (
        ValidationError,
        HTTPError,
        NetworkError,
        FileSystemError,
        PaperDLError,
    ) as e:
        _handle_error(e, quiet=quiet)
    except Exception as e:
        _handle_error(e, quiet=quiet)


if __name__ == "__main__":
    main()
