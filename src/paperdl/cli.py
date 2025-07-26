# ABOUTME: Command-line interface for paper-dl using Click framework
# ABOUTME: Handles argument parsing, validation, and main entry point

import click


@click.command()
@click.argument('url')
@click.option('--dir', default=None, help='Download directory (default: ~/papers/)')
@click.option('--name', default=None, help='Custom filename')
@click.option('--quiet', is_flag=True, help='Suppress output for scripting')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def main(url, dir, name, quiet, verbose):
    """Download academic papers with descriptive filenames."""
    if not quiet:
        click.echo(f"→ Downloading: {url}")
    
    # TODO: Implement actual download functionality
    click.echo("✗ Download functionality not yet implemented")


if __name__ == '__main__':
    main()