# ABOUTME: CLI interface tests for paper-dl command-line functionality
# ABOUTME: Tests argument parsing, help text, and basic command execution

from click.testing import CliRunner

from paperdl.cli import main


def test_cli_help():
    """Test CLI help output contains expected content."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Download academic papers with descriptive filenames" in result.output
    assert "--dir" in result.output
    assert "--name" in result.output
    assert "--quiet" in result.output
    assert "--verbose" in result.output


def test_cli_requires_url():
    """Test CLI fails gracefully when no URL provided."""
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Usage:" in result.output


def test_cli_with_url():
    """Test CLI accepts URL argument and downloads successfully."""
    runner = CliRunner()
    result = runner.invoke(main, ["https://arxiv.org/abs/2301.00001"])

    # Should show downloading message and success
    assert "Downloading: https://arxiv.org/abs/2301.00001" in result.output
    assert "Downloaded to:" in result.output
    assert result.exit_code == 0
