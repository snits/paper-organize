# Paper-DL Implementation Roadmap

## Project Overview
Command-line utility for downloading academic papers with descriptive filenames instead of cryptic identifiers.

## Implementation Milestones

### Milestone 1: Basic Download Functionality (Week 1)
**Goal**: Core download capability with minimal features

**Tasks**:
1. **Project Setup** (Day 1)
   - Initialize Python project with uv
   - Setup src/ layout project structure
   - Initialize git repository
   - Add MIT license
   - Configure development environment
   - Create basic CLI entry point with click

2. **HTTP Download Module** (Day 2-3)
   - Implement basic URL download with requests
   - Add progress bar for downloads
   - Basic retry logic for network failures
   - Save to current directory with original filename

3. **CLI Interface** (Day 3-4)
   - Command parsing with click: `paper-dl <url>`
   - Basic argument validation
   - Help text and usage examples
   - Error handling for invalid URLs

4. **Basic Testing** (Day 4-5)
   - Unit tests for download module
   - CLI integration tests
   - Test with sample arXiv URLs
   - Error case testing

**Deliverable**: Working CLI that downloads PDFs to current directory
**Success Criteria**: `paper-dl https://arxiv.org/pdf/2301.00001.pdf` downloads file

### Milestone 2: Smart Naming (Week 2-3)
**Goal**: Extract metadata and generate readable filenames

**Tasks**:
1. **PDF Text Extraction** (Day 6-8)
   - Add PyPDF2 or pdfplumber dependency
   - Extract first page text from PDF
   - Parse title from text (usually first large text block)
   - Parse authors (usually follows title)
   - Handle extraction failures gracefully

2. **Filename Generation** (Day 9-10)
   - Implement naming template: `{year}-{author}-{title-slug}.pdf`
   - Sanitize special characters for filesystem
   - Truncate long titles to reasonable length
   - Fallback to URL-based naming if extraction fails

3. **Conflict Resolution** (Day 11-12)
   - Check for existing files before saving
   - Append numbers for duplicates: `filename(2).pdf`
   - Provide user feedback for conflicts
   - Option to overwrite existing files

4. **Enhanced Testing** (Day 12-13)
   - Test metadata extraction accuracy
   - Test filename generation edge cases
   - Test conflict resolution logic
   - Integration tests with real papers

**Deliverable**: CLI generates readable filenames automatically
**Success Criteria**: Downloads create files like `2023-vaswani-attention-is-all-you-need.pdf`

### Milestone 3: Polish & Configuration (Week 4)
**Goal**: Production-ready tool with configuration options

**Tasks**:
1. **Configuration System** (Day 14-15)
   - Default download directory: `~/papers/`
   - Configuration file support: `~/.paper-dl.yaml`
   - Environment variable support
   - Command-line flag overrides

2. **Enhanced CLI Features** (Day 15-16)
   - `--dir` flag for custom download location
   - `--name` flag for custom filename
   - `--quiet` flag for script use
   - `--verbose` flag for debugging

3. **Error Handling & UX** (Day 16-17)
   - Comprehensive error messages with suggested actions
   - Progress indicators for slow downloads
   - Validation for URLs and file paths
   - Graceful handling of permission errors

4. **Documentation & Distribution** (Day 17-18)
   - README with installation and usage
   - Man page or help documentation
   - Package for PyPI distribution
   - Git repository setup for GitHub/GitLab
   - CI/CD pipeline configuration

**Deliverable**: Production-ready tool with full feature set
**Success Criteria**: Tool works reliably for daily use with good UX

## Risk Mitigation Strategies

### Technical Risks
- **PDF extraction failures**: Implement robust fallback to URL-based naming
- **Network timeouts**: Add configurable retry logic with exponential backoff
- **Special characters**: Comprehensive filename sanitization
- **Permission errors**: Clear error messages with suggested solutions

### Project Risks
- **Scope creep**: Stick to "good enough" metadata - avoid perfect extraction
- **Overengineering**: Simple Python modules, avoid complex abstractions
- **Testing gaps**: Focus testing on real-world arXiv URLs

## Development Approach

### Testing Strategy
- **Unit tests**: Core logic (naming, extraction, config)
- **Integration tests**: Full CLI commands with fixture URLs
- **Manual testing**: Real arXiv papers throughout development

### Quality Gates
- All tests pass before milestone completion
- Manual testing with 5+ different arXiv papers
- Code review of each milestone before proceeding

### Tools & Dependencies
- **Language**: Python 3.8+
- **Package Manager**: uv (modern, fast Python package management)
- **Project Structure**: src/ layout for best practices
- **CLI**: Click framework
- **HTTP**: requests with retry logic
- **PDF**: PyPDF2 or pdfplumber
- **Config**: YAML support
- **Testing**: pytest
- **Version Control**: git
- **License**: MIT License

## Success Metrics
1. **Functionality**: Downloads and renames papers correctly 95%+ of the time
2. **Usability**: Single command covers 90% of use cases
3. **Reliability**: Handles network errors and edge cases gracefully
4. **Performance**: Downloads complete in reasonable time with progress feedback

## Post-Implementation Considerations
- **Future sources**: Architecture supports adding bioRxiv, SSRN, etc.
- **Batch processing**: Current design supports `xargs` for multiple URLs
- **Metadata improvement**: Can enhance extraction without breaking interface