# Paper-DL Tool Specification

## Executive Summary
A command-line utility that downloads academic papers from URLs and automatically renames them with descriptive filenames instead of cryptic identifiers.

## Problem Statement
Academic papers downloaded from sources like arXiv.org have cryptic filenames (e.g., `2301.00001.pdf`) that provide no information about the paper's content. Users need descriptive filenames to easily identify papers weeks or months later.

## Core Requirements

### Functional Requirements
1. **Download papers** from academic URLs (starting with arXiv)
2. **Extract metadata** (title, authors, year) from downloaded PDFs
3. **Generate readable filenames** using extracted metadata
4. **Store files** in a configurable location with conflict resolution
5. **Provide clear feedback** on download progress and errors

### Non-Functional Requirements
- **Performance**: Handle single downloads efficiently (primary use case)
- **Reliability**: Graceful error handling and fallback mechanisms  
- **Usability**: Zero-config operation with optional customization
- **Maintainability**: Simple, testable Python codebase
- **Portability**: Linux and macOS support

## User Interface Design

### Command Structure
```bash
# Primary usage pattern
paper-dl <url>

# Extended usage with options
paper-dl <url> [--dir PATH] [--name FILENAME] [--quiet] [--verbose]
```

### Examples
```bash
# Basic download
paper-dl https://arxiv.org/abs/2301.00001

# Custom directory
paper-dl https://arxiv.org/abs/2301.00001 --dir ~/research/transformers

# Custom filename
paper-dl https://arxiv.org/abs/2301.00001 --name "attention-mechanism-paper"

# Quiet mode for scripting
paper-dl --quiet https://arxiv.org/abs/2301.00001
```

### User Feedback Design
```bash
# Normal operation
$ paper-dl https://arxiv.org/abs/2301.00001
→ Fetching paper metadata...
→ "Attention Is All You Need" by Vaswani et al. (2017)
→ Downloading PDF... [████████████████████] 100% (2.3MB)
✓ Saved: ~/papers/2017-vaswani-attention-is-all-you-need.pdf

# Error handling
$ paper-dl https://arxiv.org/abs/invalid
✗ Could not fetch paper: ArXiv ID not found
  Try checking the URL or paper ID
```

## Technical Architecture

### Technology Stack
- **Language**: Python 3.8+
- **Package Manager**: uv (modern, fast dependency management)
- **Project Structure**: src/ layout for best practices
- **CLI Framework**: Click
- **HTTP Library**: requests with retry logic
- **PDF Processing**: PyPDF2 or pdfplumber
- **Configuration**: YAML support
- **Testing**: pytest
- **Version Control**: git
- **License**: MIT License (open source)

### Component Architecture
```
paper-dl/
├── src/
│   └── paperdl/
│       ├── __init__.py
│       ├── cli.py          # Click interface, argument parsing
│       ├── download.py     # HTTP download with retry/progress  
│       ├── metadata.py     # PDF text extraction, filename generation
│       ├── storage.py      # File operations, conflict resolution
│       └── exceptions.py   # Error handling
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml         # uv project configuration
├── README.md              # Project documentation
└── LICENSE                # MIT License
```

### Data Flow
1. **URL Input** → Validate and parse URL
2. **Download** → Fetch PDF with progress indication
3. **Extract** → Parse title/authors from PDF text
4. **Generate** → Create filesystem-safe filename
5. **Store** → Save with conflict resolution

## Metadata Extraction Strategy

### Approach
"Good enough" extraction focused on readable filenames rather than perfect metadata.

### Extraction Methods (in priority order)
1. **PDF text parsing**: Extract title and first author from first page
2. **URL fallback**: Use URL components if PDF extraction fails
3. **Original filename**: Last resort preservation

### Filename Template
Default format: `{year}-{first-author-last}-{title-slug}.pdf`

Examples:
- `2017-vaswani-attention-is-all-you-need.pdf`
- `2018-devlin-bert-pretraining-transformers.pdf`

### Sanitization Rules
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters: `[<>:"/\\|?*]`
- Limit title length to 50 characters
- Handle conflicts with numeric suffixes: `filename(2).pdf`

## Configuration Management

### Default Behavior (Zero-Config)
- **Download directory**: `~/papers/` (created if doesn't exist)
- **Naming format**: `{year}-{author}-{title-slug}.pdf`
- **Conflict resolution**: Append numbers for duplicates
- **Progress display**: Show progress bar for downloads

### Configuration Options
```yaml
# ~/.paper-dl.yaml (optional)
default_dir: ~/research/papers
naming_format: "{year}-{authors}-{title}"
max_title_length: 50
show_progress: true
```

### Environment Variables
```bash
export PAPER_DL_DIR=~/current-research
export PAPER_DL_QUIET=true
```

## Error Handling Strategy

### Error Categories
1. **User Errors**: Invalid URLs, permission issues
2. **Network Errors**: Timeouts, server errors
3. **Processing Errors**: PDF parsing failures, metadata extraction issues

### Error Response Pattern
- **Clear description** of what went wrong
- **Suggested action** for user to take
- **Graceful fallbacks** when possible
- **Appropriate exit codes** for scripting

### Retry Logic
- Network timeouts: 3 retries with exponential backoff
- Server errors (5xx): 2 retries with delay
- Client errors (4xx): No retry, immediate error

## Quality Assurance

### Testing Strategy
- **Unit Tests**: Core logic components (metadata, naming, config)
- **Integration Tests**: Full CLI execution with fixture URLs
- **Manual Testing**: Real arXiv papers during development

### Success Criteria
- **Functionality**: 95%+ success rate with arXiv papers
- **Reliability**: Handles network failures gracefully
- **Usability**: Single command covers 90% of use cases
- **Performance**: Reasonable download times with progress feedback

### Test Cases
- Valid arXiv URLs with various paper types
- Invalid URLs and network error conditions
- PDF files with unusual formatting or metadata
- Filesystem permission and storage issues
- Configuration file parsing and validation

## Deployment & Distribution

### Installation Methods
1. **PyPI package**: `uv add paper-dl` or `pip install paper-dl`
2. **GitHub/GitLab releases**: Pre-built Python wheels
3. **Development**: `git clone` and `uv sync` for local installation

### System Requirements
- Python 3.8 or higher
- Internet connection for downloads
- Write permissions to download directory

## Success Metrics

### Primary Goals
1. **Ease of use**: Single command downloads and renames papers
2. **Reliability**: Consistent operation across different paper sources
3. **Maintainability**: Simple codebase that's easy to extend

### Performance Targets
- Download initiation: < 2 seconds
- Metadata extraction: < 1 second for typical papers
- Error feedback: Immediate with clear messaging

## Future Extensibility

### Additional Sources
Architecture supports adding new academic paper sources:
- bioRxiv, SSRN, IEEE Xplore, etc.
- Each source implements standardized interface
- Source-specific configuration options

### Feature Enhancements
- Batch processing multiple URLs
- Enhanced metadata extraction
- Integration with reference managers
- Custom naming templates

## Risk Analysis

### Technical Risks
- **PDF parsing failures**: Mitigated by fallback naming strategies
- **Network reliability**: Handled by retry logic and clear error messages
- **File system issues**: Comprehensive permission and space checking

### Mitigation Strategies
- Extensive testing with real-world papers
- Graceful degradation when components fail
- Clear documentation and error messages
- Simple architecture to minimize complexity