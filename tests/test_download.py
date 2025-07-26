# ABOUTME: Download module tests for HTTP functionality and retry logic
# ABOUTME: Tests file downloading, progress reporting, and error handling

import pytest
from paperdl.download import download_file


def test_download_file_not_implemented():
    """Test download_file raises NotImplementedError until implemented."""
    with pytest.raises(NotImplementedError):
        download_file('https://example.com/file.pdf', '/tmp/test.pdf')