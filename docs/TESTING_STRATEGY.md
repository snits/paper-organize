# Testing Strategy Migration

## Overview

This document explains the migration from unreliable external service-based integration tests to a robust local testing infrastructure.

## Problems with Previous Approach

### External Service Dependencies (httpbin.org)
- **Reliability Issues**: Service availability inconsistent in CI environments
- **Performance Problems**: Real network requests taking 40+ seconds
- **Invalid Test Data**: Random binary data instead of valid PDFs
- **Unpredictable Behavior**: 503 errors instead of expected responses

### Test Failures
The old integration tests were failing because:
1. `httpbin.org/bytes/N` returns random binary data, not valid PDFs
2. PDF metadata extraction fails on invalid data
3. File naming logic breaks when content can't be processed
4. External service can be temporarily unavailable

## New Reliable Testing Infrastructure

### Key Components

#### 1. Local HTTP Server (`pytest-httpserver`)
- **Controlled Responses**: Exact control over HTTP status codes, headers, content
- **Speed**: Local responses are nearly instantaneous
- **Reliability**: No external network dependencies
- **Realistic Testing**: Uses proper PDF content and headers

#### 2. Test Fixtures (`tests/fixtures/`)
- **`test_paper_minimal.pdf`**: Minimal valid PDF for basic testing
- **`test_paper_with_metadata.pdf`**: PDF with extractable metadata (title, author)
- **Helper functions**: Utilities for creating test scenarios

#### 3. HTTP Test Helpers (`tests/http_test_helpers.py`)
- **`setup_pdf_response()`**: Create PDF download endpoints
- **`setup_error_response()`**: Create HTTP error scenarios
- **`HTTPScenarios`**: Pre-configured common test patterns

#### 4. Shared Fixtures (`tests/conftest.py`)
- **`http_server`**: Local HTTP server for all tests
- **`temp_dir`**: Clean temporary directories
- **`pdf_fixture_*`**: Various PDF content types

### Benefits

#### Performance Improvements
- **43% faster**: 24 seconds vs 42 seconds for same test coverage
- **No network delays**: Local server responses are instant
- **Predictable timing**: No waiting for external service responses

#### Reliability Improvements
- **100% test success rate**: All tests pass consistently
- **No external dependencies**: Works in any CI environment
- **Controlled test data**: Valid PDFs with known characteristics

#### Maintainability Improvements
- **Easier debugging**: Full control over server responses
- **Better error testing**: Can simulate exact error conditions
- **Comprehensive coverage**: Test scenarios impossible with external services

## Test Categories

### HTTP Response Testing
```python
def test_successful_download_with_local_server(self, http_server, pdf_fixture_minimal, temp_dir):
    test_url = setup_pdf_response(http_server, "/test.pdf", pdf_fixture_minimal)
    # ... test logic
```

### Error Scenario Testing
```python
def test_http_404_error_handling(self, http_server, temp_dir):
    test_url = setup_error_response(http_server, "/missing.pdf", 404)
    # ... test logic
```

### File Processing Testing
```python
def test_auto_naming_with_valid_pdf(self, http_server, pdf_fixture_with_metadata, temp_dir):
    # Tests metadata extraction with known PDF content
    # ... test logic
```

## Migration Guidelines

### For New Tests
1. **Use fixtures**: Always use `http_server` and `temp_dir` fixtures
2. **Use helpers**: Leverage `http_test_helpers.py` utilities
3. **Test real scenarios**: Use valid PDF fixtures, not random data
4. **Control responses**: Set exact HTTP status codes and headers

### For Existing Tests
1. **Replace httpbin.org URLs**: Use local server endpoints
2. **Use valid test data**: Replace random bytes with PDF fixtures
3. **Add proper assertions**: Check file content, not just existence
4. **Handle edge cases**: Test with known, controlled data

## Running Tests

### Standard Integration Tests
```bash
# All integration tests (fast and reliable)
uv run pytest tests/test_integration_reliable.py

# Specific test class
uv run pytest tests/test_integration_reliable.py::TestCLIIntegrationReliable

# With coverage
uv run pytest tests/test_integration_reliable.py --cov
```

### Performance Tests
```bash
# Include slow performance tests
uv run pytest tests/test_integration_reliable.py -m slow

# Exclude slow tests for faster CI
uv run pytest tests/test_integration_reliable.py -m "not slow"
```

### Comparison with Old Tests
```bash
# New reliable tests (recommended)
time uv run pytest tests/test_integration_reliable.py -q

# Old external tests (deprecated)  
time uv run pytest tests/test_integration.py -q
```

## Files in Testing Infrastructure

```
tests/
├── conftest.py                    # Shared fixtures
├── http_test_helpers.py          # HTTP testing utilities
├── test_integration_reliable.py # New reliable integration tests
├── test_integration.py          # Old external tests (deprecated)
└── fixtures/
    ├── test_paper_minimal.pdf       # Minimal valid PDF
    └── test_paper_with_metadata.pdf # PDF with metadata
```

## Quality Gates

All tests must pass before committing:
```bash
# Type checking
uv run mypy src/ tests/

# Linting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Tests (including new integration tests)
uv run pytest
```

The new testing infrastructure ensures that integration tests are fast, reliable, and thoroughly exercise real application behavior without external dependencies.