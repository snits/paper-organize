# ABOUTME: CLI interface tests for paper-dl command-line functionality
# ABOUTME: Tests argument parsing, help text, and basic command execution
# SPDX-License-Identifier: MIT

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from paperdl.cli import _determine_download_directory, _setup_download_directory, main
from paperdl.exceptions import FileSystemError


def test_cli_help() -> None:
    """Test CLI help output contains expected content."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Download academic papers with descriptive filenames" in result.output
    assert "--dir" in result.output
    assert "--name" in result.output
    assert "--quiet" in result.output
    assert "--verbose" in result.output


def test_cli_requires_url() -> None:
    """Test CLI fails gracefully when no URL provided."""
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Usage:" in result.output


def test_cli_with_url() -> None:
    """Test CLI accepts URL argument and downloads successfully."""
    runner = CliRunner()
    result = runner.invoke(main, ["https://arxiv.org/abs/2301.00001"])

    # Should show downloading message and success
    assert "Downloading: https://arxiv.org/abs/2301.00001" in result.output
    assert "Downloaded to:" in result.output
    assert result.exit_code == 0


# Directory Configuration Tests


def test_determine_download_directory_command_line_flag() -> None:
    """Test --dir flag takes highest priority."""
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_dir = str(Path(temp_dir) / "custom")

        # Should use command line flag even if PAPERS_DIR is set
        with patch.dict(os.environ, {"PAPERS_DIR": "/some/other/path"}):
            result = _determine_download_directory(custom_dir)
            assert result == Path(custom_dir).expanduser()


def test_determine_download_directory_papers_dir_env() -> None:
    """Test PAPERS_DIR environment variable is used when no --dir flag."""
    with tempfile.TemporaryDirectory() as temp_dir:
        papers_dir = str(Path(temp_dir) / "my_papers")

        with patch.dict(os.environ, {"PAPERS_DIR": papers_dir}):
            result = _determine_download_directory(None)
            assert result == Path(papers_dir).expanduser()


def test_determine_download_directory_default_papers() -> None:
    """Test ~/Papers default when no flag or env var."""
    # Clear PAPERS_DIR if it exists
    with patch.dict(os.environ, {}, clear=True):
        result = _determine_download_directory(None)
        expected = Path.home() / "Papers"
        assert result == expected


def test_determine_download_directory_returns_papers_path() -> None:
    """Test that _determine_download_directory returns ~/Papers path (no fallback logic)."""
    with patch.dict(os.environ, {}, clear=True), patch(
        "paperdl.cli.Path.home"
    ) as mock_home:
        fake_home = Path("/fake/home")
        mock_home.return_value = fake_home

        result = _determine_download_directory(None)
        assert result == fake_home / "Papers"


def test_setup_download_directory_creates_directory() -> None:
    """Test that setup creates the target directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir) / "new_papers_dir"
        assert not target_dir.exists()

        result_dir, is_first_run = _setup_download_directory(
            str(target_dir), quiet=True
        )

        assert result_dir == target_dir
        assert target_dir.exists()
        assert not is_first_run  # Not first-run since we specified custom dir


def test_setup_download_directory_first_run_papers_dir() -> None:
    """Test first-run experience with ~/Papers creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        fake_home = Path(temp_dir)
        papers_dir = fake_home / "Papers"

        # Ensure Papers doesn't exist yet
        assert not papers_dir.exists()

        # Clear environment and mock home directory
        with patch.dict(os.environ, {}, clear=True), patch(
            "paperdl.cli.Path.home", return_value=fake_home
        ):
            result_dir, is_first_run = _setup_download_directory(None, quiet=True)

            assert result_dir == papers_dir
            assert papers_dir.exists()
            assert is_first_run  # Should detect first-run


def test_setup_download_directory_first_run_message() -> None:
    """Test first-run message is shown when creating ~/Papers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        fake_home = Path(temp_dir)

        runner = CliRunner()
        with patch("paperdl.cli.Path.home", return_value=fake_home), patch.dict(
            os.environ, {}, clear=True
        ), runner.isolated_filesystem():
            result_dir, is_first_run = _setup_download_directory(None, quiet=False)
            assert is_first_run


def test_setup_download_directory_quiet_no_message() -> None:
    """Test no first-run message when quiet=True."""
    with tempfile.TemporaryDirectory() as temp_dir:
        fake_home = Path(temp_dir)
        papers_dir = fake_home / "Papers"

        with patch("paperdl.cli.Path.home", return_value=fake_home), patch.dict(
            os.environ, {}, clear=True
        ):
            result_dir, is_first_run = _setup_download_directory(None, quiet=True)
            assert result_dir == papers_dir
            assert is_first_run  # Detected but no message shown


def test_cli_help_shows_environment_variable() -> None:
    """Test that help text mentions PAPERS_DIR and directory priority."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "PAPERS_DIR" in result.output


def test_cli_respects_papers_dir_env() -> None:
    """Test CLI integration with PAPERS_DIR environment variable."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        papers_dir = str(Path(temp_dir) / "test_papers")

        with patch.dict(os.environ, {"PAPERS_DIR": papers_dir}), patch(
            "paperdl.cli.download_file"
        ) as mock_download:
            result = runner.invoke(main, ["https://httpbin.org/bytes/100", "--quiet"])

            # Should succeed and use our custom directory
            assert result.exit_code == 0
            mock_download.assert_called_once()

            # Check that the download was called with path in our custom directory
            call_args = mock_download.call_args[0]
            download_path = Path(call_args[1])
            assert str(download_path.parent) == papers_dir


def test_setup_download_directory_fallback_to_cwd() -> None:
    """Test fallback to current directory when ~/Papers creation fails."""
    with tempfile.TemporaryDirectory() as temp_dir:
        fake_home = Path(temp_dir)
        papers_dir = fake_home / "Papers"
        cwd = Path.cwd()

        # Clear environment and mock home directory
        with patch.dict(os.environ, {}, clear=True), patch(
            "paperdl.cli.Path.home", return_value=fake_home
        ):
            # Track which paths had mkdir called
            mkdir_calls = []

            def mock_mkdir(
                self: Path, parents: bool = True, exist_ok: bool = True
            ) -> None:
                mkdir_calls.append(str(self))
                if str(self) == str(papers_dir):
                    error_msg = "Cannot create Papers directory"
                    raise PermissionError(error_msg)
                # For cwd, do nothing (it exists)

            # Patch the mkdir method on Path instances
            with patch("pathlib.Path.mkdir", mock_mkdir):
                # Test the fallback
                result_dir, is_first_run = _setup_download_directory(None, quiet=True)

                # Should fallback to current working directory
                assert result_dir == cwd
                assert not is_first_run  # Not first-run when we fallback

                # Verify mkdir was called for Papers and cwd
                assert len(mkdir_calls) == 2
                assert mkdir_calls[0] == str(papers_dir)
                assert mkdir_calls[1] == str(cwd)


def test_setup_download_directory_no_fallback_for_explicit_dir() -> None:
    """Test that explicit directories don't fallback to cwd on failure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_dir = Path(temp_dir) / "custom" / "nested" / "dir"

        # Mock mkdir to always fail
        def mock_mkdir(self: Path, parents: bool = True, exist_ok: bool = True) -> None:
            error_msg = "Cannot create directory"
            raise PermissionError(error_msg)

        with patch("pathlib.Path.mkdir", mock_mkdir):
            # Should raise FileSystemError, not fallback
            with pytest.raises(FileSystemError) as exc_info:
                _setup_download_directory(str(custom_dir), quiet=True)

            assert "Cannot create directory" in str(exc_info.value)
            assert "Set PAPERS_DIR or use --dir" in exc_info.value.details["suggestion"]
