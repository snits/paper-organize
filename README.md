# paper-dl

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

A command-line utility for downloading academic papers with intelligent metadata extraction and descriptive filenames.

## Features

- **Smart Naming**: Automatically extracts metadata from PDFs and generates readable filenames like `Wang_Hierarchical_Reasoning_Model.pdf`
- **Network Resilience**: Built-in retry logic with exponential backoff for network failures  
- **Progress Tracking**: Real-time download progress with size information
- **Conflict Resolution**: Automatic handling of filename conflicts with numbered suffixes
- **Graceful Fallbacks**: Works even when metadata extraction fails
- **Type Safe**: Full MyPy compliance with comprehensive type annotations

## Installation

### From Source
```bash
git clone <repository-url>
cd paper-dl
pip install -e .
```

### Development Installation
```bash
git clone <repository-url>
cd paper-dl
uv sync --extra dev
```

## Usage

### Basic Usage
```bash
# Download with automatic intelligent naming
paper-dl https://arxiv.org/pdf/2506.21734

# Download with original filename  
paper-dl https://arxiv.org/pdf/2506.21734 --no-auto-name
```

### Real Example
```bash
# Download this arXiv paper:
paper-dl https://arxiv.org/pdf/2506.21734

# Creates file: Wang_Hierarchical_Reasoning_Model.pdf
# Instead of: 2506.21734.pdf
```

### Command Options
```bash
paper-dl --help

# Usage: paper-dl [OPTIONS] URL
# 
# Options:
#   --dir DIRECTORY   Directory to save file to (overrides PAPERS_DIR)
#   --name TEXT       Custom filename for the download  
#   --no-auto-name    Skip metadata extraction and use original filename
#   --quiet          Suppress output for scripting
#   --verbose        Show detailed output
#   --help           Show this message and exit
#
# Directory Priority: --dir > PAPERS_DIR environment variable > ~/Papers (default)
```

### Environment Variables
```bash
# Set default download directory
export PAPERS_DIR="$HOME/Research/Papers"

# Now all downloads go to ~/Research/Papers by default
paper-dl https://arxiv.org/pdf/2506.21734

# Override for specific download
paper-dl https://arxiv.org/pdf/2506.21734 --dir ./references/
```

## How It Works

1. **Downloads** the PDF from the provided URL with progress tracking
2. **Extracts metadata** using a layered strategy:
   - PyPDF for basic PDF metadata
   - pdf2doi for academic identifiers (DOI, arXiv ID)
   - Title parsing from PDF text as fallback
3. **Generates filename** in format: `{FirstAuthor}_{Year}_{Title}.pdf`
4. **Sanitizes** filename for filesystem compatibility
5. **Resolves conflicts** by appending numbers if file exists

## Requirements

- Python 3.8+
- Internet connection for downloads

## Development

```bash
# Install development dependencies
uv sync --extra dev

# Run tests (74 tests)
uv run pytest

# Type checking
uv run mypy src/ tests/

# Linting and formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Project Quality Metrics
- **Test Coverage**: 74/74 tests passing
- **Type Safety**: Full MyPy compliance with `py.typed` marker
- **Code Quality**: Ruff linting with comprehensive rule set
- **License Compliance**: SPDX identifiers in all source files

## Acknowledgments

This project builds on several excellent open-source libraries:

### Core Dependencies

- **[pypdf](https://github.com/py-pdf/pypdf)** (BSD-3-Clause) - Pure Python PDF library for metadata extraction
- **[pdf2doi](https://github.com/MicheleCotrufo/pdf2doi)** (MIT) - Academic paper identifier extraction (DOI, arXiv ID)
- **[Click](https://github.com/pallets/click)** (BSD-3-Clause) - Command-line interface framework
- **[Requests](https://github.com/psf/requests)** (Apache-2.0) - HTTP library for downloads
- **[tqdm](https://github.com/tqdm/tqdm)** (MIT/MPL-2.0) - Progress bar library

### Development Dependencies

- **[pytest](https://github.com/pytest-dev/pytest)** (MIT) - Testing framework
- **[MyPy](https://github.com/python/mypy)** (MIT) - Static type checker
- **[Ruff](https://github.com/astral-sh/ruff)** (MIT) - Fast Python linter and formatter

We're grateful to the maintainers and contributors of these projects for making paper-dl possible.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTORS.md](CONTRIBUTORS.md) for:
- Code of conduct
- Development workflow
- Contribution guidelines  
- Recognition of contributors

For questions or discussions, please open an issue.