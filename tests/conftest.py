# ABOUTME: Shared test fixtures and utilities for paper-organize testing
# ABOUTME: Provides HTTP server fixtures and test data for reliable CI testing
# SPDX-License-Identifier: MIT

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from pytest_httpserver import HTTPServer
from werkzeug import Response


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def http_server() -> Generator[HTTPServer, None, None]:
    """Create local HTTP server for testing without external dependencies."""
    server = HTTPServer(host="127.0.0.1", port=0)  # Random available port
    server.start()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def pdf_fixture_minimal() -> bytes:
    """Return minimal valid PDF content for testing."""
    return (Path(__file__).parent / "fixtures" / "test_paper_minimal.pdf").read_bytes()


@pytest.fixture
def pdf_fixture_with_metadata() -> bytes:
    """Return PDF content with extractable metadata for testing."""
    return (
        Path(__file__).parent / "fixtures" / "test_paper_with_metadata.pdf"
    ).read_bytes()


@pytest.fixture
def large_pdf_content() -> bytes:
    """Generate larger PDF content for testing chunked downloads."""
    # Create a minimal but larger PDF by padding with whitespace
    base_content = (
        Path(__file__).parent / "fixtures" / "test_paper_minimal.pdf"
    ).read_bytes()
    # Add padding to make it larger for testing progress bars
    padding = b" " * (10240 - len(base_content))  # Make it ~10KB
    return base_content + padding


@pytest.fixture
def invalid_binary_data() -> bytes:
    """Return invalid binary data that isn't a PDF."""
    return b"This is not a PDF file\x00\x01\x02\x03" * 100


@pytest.fixture
def server_error_response() -> Response:
    """Create server error response for testing."""
    return Response(
        "Internal Server Error - Something went wrong",
        status=500,
        headers={"Content-Type": "text/html"},
    )


@pytest.fixture
def not_found_response() -> Response:
    """Create 404 not found response for testing."""
    return Response(
        "Not Found - The requested resource was not found",
        status=404,
        headers={"Content-Type": "text/html"},
    )
