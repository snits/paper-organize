# ABOUTME: Command-line interface for paper-dl using Click framework
# ABOUTME: Handles argument parsing, validation, and main entry point

from pathlib import Path
from urllib.parse import urlparse

import click

from .download import download_file
from .exceptions import PaperDLError, NetworkError, HTTPError, FileSystemError, ValidationError


@click.command()
@click.argument("url")
@click.option("--dir", "directory", default=None, help="Download directory (default: ~/papers/)")
@click.option("--name", default=None, help="Custom filename")
@click.option("--quiet", is_flag=True, help="Suppress output for scripting")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def main(url: str, directory: str | None, name: str | None, *, quiet: bool, verbose: bool) -> None:  # noqa: ARG001
    """Download academic papers with descriptive filenames."""
    if not quiet:
        click.echo(f"→ Downloading: {url}")

    try:
        # Set up download directory
        if directory is None:
            download_dir = Path.home() / "papers"
        else:
            download_dir = Path(directory).expanduser()
        
        download_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if name is None:
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename or not filename.endswith('.pdf'):
                filename = "paper.pdf"
        else:
            filename = name
            if not filename.endswith('.pdf'):
                filename += ".pdf"

        # Construct full destination path
        destination_path = download_dir / filename

        # Perform download
        download_file(url, str(destination_path))
        
        if not quiet:
            click.echo(f"✓ Downloaded to: {destination_path}")

    except ValidationError as e:
        click.echo(f"✗ {e.user_message()}", err=True)
        raise click.Abort()
    except HTTPError as e:
        click.echo(f"✗ {e.user_message()}", err=True)
        raise click.Abort()
    except NetworkError as e:
        click.echo(f"✗ {e.user_message()}", err=True)
        raise click.Abort()
    except FileSystemError as e:
        click.echo(f"✗ {e.user_message()}", err=True)
        raise click.Abort()
    except PaperDLError as e:
        click.echo(f"✗ {e.user_message()}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
