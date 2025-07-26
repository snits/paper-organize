# ABOUTME: Command-line interface for paper-dl using Click framework
# ABOUTME: Handles argument parsing, validation, and main entry point

import click


@click.command()
@click.argument("url")
@click.option("--dir", "directory", default=None, help="Download directory (default: ~/papers/)")
@click.option("--name", default=None, help="Custom filename")
@click.option("--quiet", is_flag=True, help="Suppress output for scripting")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def main(url: str, directory: str | None, name: str | None, *, quiet: bool, verbose: bool) -> None:  # noqa: ARG001
    """Download academic papers with descriptive filenames."""
    # TODO(claude): Use dir, name, verbose parameters when implementing full functionality
    if not quiet:
        click.echo(f"→ Downloading: {url}")

    # TODO(claude): Implement actual download functionality
    click.echo("✗ Download functionality not yet implemented")


if __name__ == "__main__":
    main()
