# ABOUTME: HTTP testing utilities for reliable integration testing
# ABOUTME: Provides helper functions for setting up HTTP server responses and scenarios
# SPDX-License-Identifier: MIT

from typing import Dict, Optional, Union

from pytest_httpserver import HTTPServer
from werkzeug import Request, Response


def setup_pdf_response(
    server: HTTPServer,
    endpoint: str,
    pdf_content: bytes,
    *,
    content_type: str = "application/pdf",
    filename: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> str:
    """Set up server to respond with PDF content at endpoint.

    Args:
        server: HTTP server instance
        endpoint: URL endpoint (e.g., "/paper.pdf")
        pdf_content: PDF file content bytes
        content_type: HTTP content type header
        filename: Optional filename for Content-Disposition header
        extra_headers: Additional HTTP headers to include

    Returns:
        Complete URL for the endpoint
    """
    headers = {"Content-Length": str(len(pdf_content))}

    if filename:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    if extra_headers:
        headers.update(extra_headers)

    server.expect_request(endpoint).respond_with_data(
        pdf_content, content_type=content_type, headers=headers
    )

    return str(server.url_for(endpoint))


def setup_error_response(
    server: HTTPServer,
    endpoint: str,
    status_code: int,
    *,
    error_message: str = "Error occurred",
    content_type: str = "text/plain",
) -> str:
    """Set up server to respond with error status at endpoint.

    Args:
        server: HTTP server instance
        endpoint: URL endpoint
        status_code: HTTP status code (404, 500, etc.)
        error_message: Error response body
        content_type: Response content type

    Returns:
        Complete URL for the endpoint
    """
    server.expect_request(endpoint).respond_with_data(
        error_message, status=status_code, content_type=content_type
    )

    return str(server.url_for(endpoint))


def setup_redirect_response(
    server: HTTPServer, from_endpoint: str, to_endpoint: str, *, status_code: int = 302
) -> str:
    """Set up server to respond with redirect.

    Args:
        server: HTTP server instance
        from_endpoint: Source endpoint that redirects
        to_endpoint: Target endpoint for redirect
        status_code: HTTP redirect status code

    Returns:
        Complete URL for the source endpoint
    """
    redirect_url = server.url_for(to_endpoint)

    server.expect_request(from_endpoint).respond_with_data(
        f"Redirecting to {redirect_url}",
        status=status_code,
        headers={"Location": redirect_url},
    )

    return str(server.url_for(from_endpoint))


def setup_large_file_response(
    server: HTTPServer,
    endpoint: str,
    size_bytes: int,
    *,
    content_type: str = "application/pdf",
    chunk_pattern: bytes = b"A",
) -> str:
    """Set up server to respond with large file for testing downloads.

    Args:
        server: HTTP server instance
        endpoint: URL endpoint
        size_bytes: Size of content to generate
        content_type: HTTP content type
        chunk_pattern: Pattern to repeat for content

    Returns:
        Complete URL for the endpoint
    """
    # Generate content by repeating pattern
    content = chunk_pattern * (size_bytes // len(chunk_pattern))
    if len(content) < size_bytes:
        content += chunk_pattern[: size_bytes - len(content)]

    return setup_pdf_response(server, endpoint, content, content_type=content_type)


def setup_slow_response(
    server: HTTPServer,
    endpoint: str,
    content: Union[str, bytes],
    delay_seconds: float,
    *,
    content_type: str = "application/pdf",
) -> str:
    """Set up server to respond slowly for timeout testing.

    Args:
        server: HTTP server instance
        endpoint: URL endpoint
        content: Response content
        delay_seconds: Delay before responding
        content_type: HTTP content type

    Returns:
        Complete URL for the endpoint
    """
    import time

    def slow_handler(request: Request) -> Response:
        time.sleep(delay_seconds)
        response_content = content.encode() if isinstance(content, str) else content

        return Response(
            response_content,
            content_type=content_type,
            headers={"Content-Length": str(len(response_content))},
        )

    server.expect_request(endpoint).respond_with_handler(slow_handler)
    return str(server.url_for(endpoint))


class HTTPScenarios:
    """Pre-configured HTTP test scenarios for common testing patterns."""

    @staticmethod
    def successful_pdf_download(server: HTTPServer, pdf_content: bytes) -> str:
        """Set up successful PDF download scenario."""
        return setup_pdf_response(
            server, "/paper.pdf", pdf_content, filename="research_paper.pdf"
        )

    @staticmethod
    def not_found_error(server: HTTPServer) -> str:
        """Set up 404 not found scenario."""
        return setup_error_response(
            server, "/missing.pdf", 404, error_message="File not found"
        )

    @staticmethod
    def server_error(server: HTTPServer) -> str:
        """Set up 500 server error scenario."""
        return setup_error_response(
            server, "/error.pdf", 500, error_message="Internal server error"
        )

    @staticmethod
    def large_download(server: HTTPServer, size_mb: int = 1) -> str:
        """Set up large file download scenario."""
        return setup_large_file_response(server, "/large.pdf", size_mb * 1024 * 1024)

    @staticmethod
    def arxiv_paper_url(
        server: HTTPServer, pdf_content: bytes, arxiv_id: str = "2401.00001"
    ) -> str:
        """Set up arXiv paper download scenario."""
        endpoint = f"/pdf/{arxiv_id}.pdf"
        return setup_pdf_response(
            server, endpoint, pdf_content, extra_headers={"Server": "nginx/1.18.0"}
        )
