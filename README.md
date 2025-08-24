# paper-organize

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

A command-line utility for organizing academic papers with intelligent metadata extraction and descriptive filenames. Supports downloading from URLs or processing existing PDF files.

## Features

- **Smart Naming**: Automatically extracts metadata from PDFs and generates readable filenames like `Wang_Hierarchical_Reasoning_Model.pdf`
- **Unified Input**: Process URLs, individual files, or entire directories of PDFs
- **Network Resilience**: Built-in retry logic with exponential backoff for network failures  
- **Progress Tracking**: Real-time download progress with size information
- **Conflict Resolution**: Automatic handling of filename conflicts with numbered suffixes
- **Graceful Fallbacks**: Works even when metadata extraction fails
- **Batch Processing**: Organize entire directories of PDFs with a single command
- **Environment Support**: Configurable default directories via environment variables

## Installation

### From Source
```bash
git clone <repository-url>
cd paper-organize
pip install -e .
```

### Development Installation
```bash
git clone <repository-url>
cd paper-organize
uv sync --extra dev
```

## Usage

### Basic Usage
```bash
# Download and organize a paper from URL
paper-organize https://arxiv.org/pdf/2506.21734

# Organize an existing PDF file
paper-organize ./downloaded-paper.pdf

# Batch organize all PDFs in a directory
paper-organize ./papers-directory/
```

### Real Example
```bash
# Download and organize this arXiv paper:
paper-organize https://arxiv.org/pdf/2506.21734

# Creates file: Wang_Hierarchical_Reasoning_Model.pdf
# Instead of: 2506.21734.pdf
```

### Command Options
```bash
paper-organize --help

# Usage: paper-organize [OPTIONS] INPUT
#
# INPUT can be:
#   • URL          Download and organize a paper from the web
#   • PDF file     Organize an existing PDF file  
#   • Directory    Batch organize all PDFs in a directory
# 
# Options:
#   --dir DIRECTORY   Directory to save organized files (overrides PAPERS_DIR)
#   --name TEXT       Custom filename for the organized file
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

# Now all organized papers go to ~/Research/Papers by default
paper-organize https://arxiv.org/pdf/2506.21734

# Override for specific operation
paper-organize https://arxiv.org/pdf/2506.21734 --dir ./references/
```


## How It Works

1. **Processes input** - downloads from URLs or reads existing files with progress tracking
2. **Extracts metadata** using a layered strategy:
   - PyPDF for basic PDF metadata
   - Enhanced extraction pipeline with arXiv API and pdfplumber for academic identifiers (DOI, arXiv ID)
   - Title parsing from PDF text as fallback
3. **Generates filename** in format: `{FirstAuthor}_{Year}_{Title}.pdf`
4. **Sanitizes** filename for filesystem compatibility
5. **Resolves conflicts** by appending numbers if file exists

## Intelligent Filename Examples

- `Wang_2024_Hierarchical_Reasoning_Model.pdf`
- `Smith_2023_Deep_Learning_Survey.pdf`
- `Chen_2024_Attention_Mechanisms_NLP.pdf`

## Advanced Usage

### Batch Processing
```bash
# Organize all PDFs in a directory
paper-organize ~/Downloads/papers/

# Output: Processes each PDF and organizes with metadata-based names
# Example output:
# → Processing existing file: paper1.pdf
# ✓ Renamed to: Wang_2024_Deep_Learning.pdf
# → Processing existing file: paper2.pdf  
# ✓ Renamed to: Smith_2023_Neural_Networks.pdf
# 📊 Summary: Processed 15 files
```

### Custom Organization
```bash
# Organize to specific directory with custom name
paper-organize arxiv-paper.pdf --dir ./references/ --name "important-paper"

# Disable automatic renaming
paper-organize https://arxiv.org/pdf/2506.21734 --no-auto-name
```

## Error Handling

The tool gracefully handles various error conditions:
- Network failures with automatic retry
- Invalid URLs or file paths  
- Permission errors
- Corrupted or non-PDF files
- Metadata extraction failures

## Development

### Running Tests
```bash
uv run pytest
```

### Type Checking
```bash
uv run mypy src/ tests/
```

### Linting and Formatting
```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Dependencies

This project builds on several excellent open-source libraries:

- **[Click](https://github.com/pallets/click)** (BSD-3-Clause) - Command line interface toolkit
- **[Requests](https://github.com/psf/requests)** (Apache-2.0) - HTTP library for downloads
- **[PyPDF](https://github.com/py-pdf/pypdf)** (BSD-3-Clause) - PDF text extraction and metadata
- **[pdfplumber](https://github.com/jsvine/pdfplumber)** (MIT) - Enhanced PDF text extraction
- **[arxiv](https://github.com/lukasschwab/arxiv.py)** (MIT) - Official arXiv API client
- **[tqdm](https://github.com/tqdm/tqdm)** (MIT/MPL-2.0) - Progress bars
- **[pytest](https://github.com/pytest-dev/pytest)** (MIT) - Testing framework
- **[MyPy](https://github.com/python/mypy)** (MIT) - Static type checker
- **[Ruff](https://github.com/astral-sh/ruff)** (MIT) - Fast Python linter and formatter

We're grateful to the maintainers and contributors of these projects for making paper-organize possible.

## License

MIT License - see LICENSE file for details.