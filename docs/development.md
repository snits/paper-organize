# ABOUTME: Development guide for paper-dl project contributors
# ABOUTME: Instructions for testing, linting, and quality assurance

# Development Guide

## Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd paper-dl

# Install development dependencies
uv sync --extra dev

# Verify installation
uv run paper-dl --help
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_download.py

# Run with coverage
uv run pytest --cov=paperdl

# Run verbose output
uv run pytest -v
```

## Code Quality Checks

```bash
# Run linting with ruff
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Format code with ruff
uv run ruff format src/ tests/

# Type checking with mypy
uv run mypy src/paperdl/
```

## Development Workflow

1. **Write failing test** following TDD approach
2. **Implement minimal code** to pass test
3. **Run quality checks**:
   ```bash
   uv run pytest          # All tests pass
   uv run ruff check      # No linting errors
   uv run mypy src/       # No type errors
   ```
4. **Commit atomic changes** with descriptive messages
5. **Repeat** for next feature increment

## Project Commands Reference

```bash
# Development setup
uv sync --extra dev                    # Install all dev dependencies
uv add <package>                       # Add runtime dependency
uv add --group dev <package>           # Add dev dependency

# Testing
uv run pytest                          # Run test suite
uv run pytest --cov=paperdl --cov-report=html  # Coverage report

# Code quality
uv run ruff check src/ tests/          # Lint check
uv run ruff format src/ tests/         # Format code
uv run mypy src/paperdl/              # Type check

# CLI testing
uv run paper-dl <url>                  # Test CLI
uv run paper-dl --help                 # Show help
```