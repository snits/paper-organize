# ABOUTME: Command-line interface for paper-dl with Click framework
# ABOUTME: Handles argument parsing, validation, and main entry point

from pathlib import Path
from urllib.parse import urlparse

import click

from .download import download_file
from .exceptions import (
    FileSystemError,
    HTTPError,
    NetworkError,
    PaperDLError,
    ValidationError,
)
from .metadata import extract_pdf_metadata, generate_filename


def _setup_download_directory(directory: str | None) -> Path:
    """Set up and return the download directory."""
    download_dir = Path.cwd() if directory is None else Path(directory).expanduser()

    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def _determine_filename(name: str | None, url: str) -> str:
    """Determine the filename for the download."""
    if name is None:
        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename or not filename.endswith(".pdf"):
            filename = "paper.pdf"
    else:
        filename = name
        if not filename.endswith(".pdf"):
            filename += ".pdf"
    return filename


def _perform_metadata_rename(file_path: Path, *, quiet: bool) -> Path:
    """Perform the actual metadata-based rename operation.

    Args:
        file_path: Current path to downloaded PDF
        quiet: Whether to suppress output messages

    Returns:
        Path: Final path after potential renaming
    """
    # Extract metadata from PDF
    metadata = extract_pdf_metadata(str(file_path))

    # Generate new filename from metadata
    new_filename = generate_filename(metadata, file_path.name)

    # If filename unchanged, return original path
    if new_filename == file_path.name:
        return file_path

    # Handle filename conflicts
    new_path = file_path.parent / new_filename
    counter = 1
    original_new_path = new_path
    while new_path.exists():
        stem = original_new_path.stem
        suffix = original_new_path.suffix
        new_path = file_path.parent / f"{stem}_{counter}{suffix}"
        counter += 1

    # Perform the rename
    file_path.rename(new_path)

    if not quiet:
        click.echo(f"✓ Renamed to: {new_path.name}")

    return new_path


def _apply_metadata_naming(file_path: Path, *, quiet: bool) -> Path:
    """Extract PDF metadata and rename file with intelligent filename.

    Args:
        file_path: Current path to downloaded PDF
        quiet: Whether to suppress output messages

    Returns:
        Path: Final path after potential renaming
    """
    try:
        return _perform_metadata_rename(file_path, quiet=quiet)
    except Exception as e:
        # If metadata extraction fails, log but don't fail the whole operation
        if not quiet:
            click.echo(f"⚠ Could not extract metadata for intelligent naming: {e}", err=True)
        return file_path


def _handle_error(e: Exception, *, quiet: bool) -> None:  # noqa: ARG001
    """Handle and report errors consistently."""
    if hasattr(e, "user_message"):
        click.echo(f"✗ {e.user_message()}", err=True)
    else:
        click.echo(f"✗ Unexpected error: {e}", err=True)
    raise click.Abort from e


@click.command()
@click.argument("url")
@click.option("--dir", "directory", help="Directory to save file to")
@click.option("--name", help="Custom filename for the download")
@click.option("--no-auto-name", is_flag=True, help="Disable automatic filename generation from PDF metadata")
@click.option("--quiet", is_flag=True, help="Suppress output for scripting")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def main(
    url: str, directory: str | None, name: str | None, *, no_auto_name: bool, quiet: bool, verbose: bool
) -> None:
    """Download academic papers with descriptive filenames."""
    del verbose  # Currently unused, but reserved for future features

    if not quiet:
        click.echo(f"→ Downloading: {url}")

    try:
        download_dir = _setup_download_directory(directory)
        filename = _determine_filename(name, url)
        destination_path = download_dir / filename

        # Perform download
        download_file(url, str(destination_path))

        if not quiet:
            click.echo(f"✓ Downloaded to: {destination_path}")

        # Apply metadata-based naming if enabled and user didn't provide custom name
        if not no_auto_name and name is None:
            final_path = _apply_metadata_naming(destination_path, quiet=quiet)
            if final_path != destination_path:
                destination_path = final_path

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
