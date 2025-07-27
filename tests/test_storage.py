# ABOUTME: Storage module tests for file operations and conflict resolution
# ABOUTME: Tests directory creation, duplicate handling, and file system operations
# SPDX-License-Identifier: MIT

import tempfile
from pathlib import Path

import pytest

from paperorganize.storage import ensure_directory, resolve_conflicts


def test_ensure_directory_creates_path() -> None:
    """Test ensure_directory creates directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "new_directory"
        assert not test_path.exists()

        ensure_directory(str(test_path))

        assert test_path.exists()
        assert test_path.is_dir()


def test_ensure_directory_handles_existing() -> None:
    """Test ensure_directory doesn't fail if directory already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        assert test_path.exists()

        # Should not raise exception
        ensure_directory(str(test_path))

        assert test_path.exists()
        assert test_path.is_dir()


def test_resolve_conflicts_not_implemented() -> None:
    """Test resolve_conflicts raises NotImplementedError until implemented."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.pdf"
        test_file.touch()  # Create existing file

        # Should raise NotImplementedError for now
        with pytest.raises(NotImplementedError):
            resolve_conflicts(str(test_file))
