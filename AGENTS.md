# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Tooling
- The project is managed with `uv`.
- The following tools are available for searching beyond the typical linux tools: rg, vgrep, fd, fzf, bat, and exa.
- mypy, and ruff are to be used for type hinting, and linting as part of the quality gating process.

# Testing
- Testing is run with pytest through uv `uv run pytest`
- Individual tests can be run with `uv run pytest tests/test_file.py::test_function`
- Test coverage: `uv run pytest --cov`

# Development Commands

## Quality Gates (Pre-commit)
```bash
# All tests must pass
uv run pytest

# Type checking must be clean  
uv run mypy src/ tests/

# Linting must pass
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Installation and Setup
```bash
# Development installation
uv sync --extra dev

# Install for local testing
pip install -e .
```

# Architecture Overview

This is a CLI utility for organizing academic papers with intelligent metadata extraction. The tool uses a **Strategy Pattern** architecture to handle three input types: URLs, local PDF files, and directories containing PDFs.

## Core Components

### Input Processing Strategy Pattern
- **URLProcessor**: Downloads papers from web URLs (arXiv, academic sites) and organizes them
- **FileProcessor**: Organizes existing PDF files with metadata-based renaming
- **DirectoryProcessor**: Batch processes all PDFs in a directory
- **Input Detection**: `input_detection.py` automatically determines input type and validates inputs

### Metadata Extraction Pipeline
Located in `metadata.py`, uses a layered approach:
1. **PyPDF**: Extracts basic PDF metadata (title, author, creation date)
2. **pdf2doi**: Identifies DOI and arXiv IDs from paper content
3. **Text parsing**: Fallback title extraction from PDF text content
4. **Filename generation**: Creates descriptive names like `Wang_2024_Hierarchical_Reasoning.pdf`

### CLI Interface (`cli.py`)
- Unified command interface with automatic processor selection
- Smart directory handling: `--dir` > `PAPERS_DIR` env var > `~/Papers` default
- Progress tracking for downloads with file size information
- Comprehensive error handling with user-friendly messages

### Key Modules
- **`download.py`**: HTTP download with retry logic and progress bars (uses requests + tqdm)
- **`storage.py`**: File operations, conflict resolution, and filesystem safety
- **`metadata_naming.py`**: Shared utilities for consistent naming across all processors
- **`exceptions.py`**: Domain-specific exception hierarchy with rich error details

## Design Patterns

### Strategy Pattern Implementation
```python
class InputProcessor(Protocol):
    def process(self, input_arg: str, destination_dir: Path, 
               custom_name: str | None, *, auto_name: bool, quiet: bool) -> list[ProcessingResult]

# Implementations: URLProcessor, FileProcessor, DirectoryProcessor
```

### Shared Utilities (DRY Principle)
All processors use `apply_metadata_naming()` from `metadata_naming.py` to ensure consistent PDF organization behavior across input types.

### Error Handling Strategy
Custom exception hierarchy (`ValidationError`, `HTTPError`, `NetworkError`, `FileSystemError`) with structured error details for better UX.

## Testing Architecture
- **Unit tests**: Individual component testing (metadata extraction, input detection)
- **Integration tests**: End-to-end workflow testing for each processor type
- **CLI tests**: Click framework testing with mock filesystem and network operations
- **Parameterized tests**: Multiple input scenarios and edge cases

## Dependencies
- **Core**: click (CLI), requests (HTTP), pypdf (PDF parsing), pdf2doi (academic metadata)
- **Progress**: tqdm (download progress bars)
- **Dev**: pytest, mypy (strict typing), ruff (linting/formatting)

# Development Standards

## Core Principles
- **Safety First**: Never execute destructive commands without confirmation
- **Smallest Viable Change**: Make the most minimal, targeted changes to accomplish the goal
- **Find the Root Cause**: Never fix a symptom without understanding the underlying issue
- **Test Everything**: All changes must be validated by tests, preferably following TDD

## Testing Requirements
**NO EXCEPTIONS POLICY**: ALL projects MUST have unit tests, integration tests, AND end-to-end tests.

**FOR EVERY NEW FEATURE OR BUGFIX, FOLLOW TDD**:
1. Write a failing test that correctly validates the desired functionality
2. Run the test to confirm it fails as expected
3. Write ONLY enough code to make the failing test pass
4. Run the test to confirm success
5. Refactor if needed while keeping tests green
6. Document any patterns or insights learned

## Code Quality Standards

### Naming Conventions
- Names MUST tell what code does, not how it's implemented or its history
- NEVER use implementation details in names (e.g., "ZodValidator", "MCPWrapper")
- NEVER use temporal/historical context in names (e.g., "NewAPI", "LegacyHandler")
- Good names tell a story about the domain: `Tool` not `AbstractToolInterface`

### Code Writing Rules
- WORK HARD to reduce code duplication, even if the refactoring takes extra effort
- MATCH the style and formatting of surrounding code within a file
- All code files MUST start with a brief 2-line comment explaining what the file does
- Each line MUST start with "ABOUTME: " to make them easily greppable
- NEVER remove code comments unless you can PROVE they are actively false

## Atomic Commit Strategy

### Commit Requirements
- **Single logical change**: One bug fix, one feature, one refactor per commit
- **Bisectable**: Each commit leaves codebase in working state
- **Self-contained**: No dependencies on future commits
- **Reversible**: Can be cleanly reverted without breaking other changes

### Commit Message Format
```
component: brief description (50 chars max)

Detailed explanation of what and why, not how.
Reference issue numbers and design decisions.
Note any breaking changes or side effects.

Co-developed-by: Name model
```

### Pre-Commit Checklist
- [ ] Builds successfully without warnings
- [ ] Existing tests pass
- [ ] New functionality has appropriate tests
- [ ] No unrelated changes mixed in
- [ ] Commit message follows format standards
- [ ] Change represents minimal viable increment

## Quality Gates
**BEFORE ANY COMMIT**:
```bash
# All tests must pass
uv run pytest

# Type checking must be clean
uv run mypy src/ tests/

# Linting must pass
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Debugging Framework
**ALWAYS find the root cause of any issue - NEVER fix symptoms**

**Phase 1: Root Cause Investigation**
- Read error messages carefully - they often contain the exact solution
- Reproduce consistently before investigating
- Check recent changes that could have caused this

**Phase 2: Pattern Analysis**
- Find working examples in the same codebase
- Compare against reference implementations
- Identify differences between working and broken code

**Phase 3: Hypothesis and Testing**
1. Form single hypothesis about root cause
2. Test minimally with smallest possible change
3. Verify before continuing - if it doesn't work, form new hypothesis
4. When you don't know something, say "I don't understand X"

**Phase 4: Implementation**
- ALWAYS have the simplest possible failing test case
- NEVER add multiple fixes at once
- ALWAYS test after each change
- IF first fix doesn't work, STOP and re-analyze

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.