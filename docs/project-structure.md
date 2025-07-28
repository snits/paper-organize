# Paper-DL Project Structure

## Current State
This document tracks the project setup and structure decisions made during planning.

## Project Directory Structure

```
paper-dl/
├── src/
│   └── paperdl/           # Main package (src/ layout)
│       ├── __init__.py
│       ├── cli.py         # Click CLI interface
│       ├── download.py    # HTTP download with progress
│       ├── metadata.py    # PDF text extraction & naming
│       ├── storage.py     # File operations & conflicts
│       └── exceptions.py  # Error handling
├── tests/                 # Test suite
├── docs/                  # Project documentation
│   ├── paper-dl-specification.md
│   ├── paper-dl-roadmap.md
│   └── project-structure.md
├── pyproject.toml         # uv project configuration
├── README.md              # Project documentation
└── LICENSE                # MIT License
```

## Technology Decisions

### Package Management
- **uv**: Modern, fast Python package manager
- **Rationale**: Faster than poetry, active development, good lock file handling

### Project Layout
- **src/ layout**: Industry best practice for Python packages
- **Benefits**: Prevents import issues during development, cleaner testing

### License
- **MIT License**: Simple, permissive open source license
- **Rationale**: Allows wide usage while requiring attribution

### Version Control
- **git**: Industry standard version control
- **Repository**: Will be hosted on GitHub or GitLab

## Next Steps

1. Initialize git repository
2. Create pyproject.toml with uv
3. Add MIT license file
4. Begin Milestone 1 implementation

## Design Principles Established

1. **Simple over complex**: "Good enough" metadata extraction
2. **Zero-config defaults**: Works out of the box
3. **Graceful fallbacks**: Always save file, even with generic name
4. **Clear error messages**: Actionable feedback for users
5. **Unix philosophy**: One tool, one job, done well