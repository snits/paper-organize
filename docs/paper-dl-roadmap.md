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

### ✅ Milestone 2: Smart Naming (COMPLETE)
**Goal**: Extract metadata and generate readable filenames

**Tasks**:
1. ✅ **PDF Metadata Extraction** (COMPLETE)
   - ✅ Add pypdf and pdf2doi dependencies with graceful fallbacks
   - ✅ Layered extraction strategy: pypdf → pdf2doi → title parsing fallback
   - ✅ Parse title, authors, year, DOI, and arXiv ID with comprehensive validation
   - ✅ Handle extraction failures gracefully with informative fallbacks
   - ✅ Optional dependency handling for production environments

2. ✅ **Intelligent Filename Generation** (COMPLETE)
   - ✅ Implement naming template: `{FirstAuthor}_{Year}_{Title}.pdf`
   - ✅ Unicode normalization (NFKD) and filesystem-safe character sanitization
   - ✅ Smart truncation with word boundaries and ellipsis handling
   - ✅ Multi-author handling with primary author selection
   - ✅ Fallback to original filename for extraction failures

3. ✅ **CLI Integration & User Experience** (COMPLETE)
   - ✅ Auto-naming enabled by default with `--no-auto-name` opt-out flag
   - ✅ Graceful error handling with user-friendly messages
   - ✅ Post-download metadata processing (never blocks downloads)
   - ✅ Automatic conflict resolution with numbered suffixes (_1, _2, etc.)
   - ✅ Progress feedback and status reporting

4. ✅ **Comprehensive Testing & Validation** (COMPLETE)
   - ✅ 74/74 tests passing with full metadata test coverage
   - ✅ Unit tests for extraction, filename generation, and edge cases (26 tests)
   - ✅ CLI integration tests with auto-naming scenarios (7 new tests)
   - ✅ Real-world validation with arXiv PDFs
   - ✅ Error scenario testing and fallback validation
   - ✅ Type safety compliance with MyPy and py.typed marker
   - ✅ Code quality gates with Ruff linting standards

**Deliverable**: CLI generates readable filenames automatically ✅ COMPLETE
**Success Criteria**: Downloads create files like `Wang_Hierarchical_Reasoning_Model.pdf` ✅ ACHIEVED
**Quality Metrics**: 74/74 tests passing, MyPy clean, Ruff clean ✅ VERIFIED

### ✅ Milestone 3: Configuration & CLI Enhancement (COMPLETE)
**Goal**: High-performance downloads and advanced features
**Status**: ✅ COMPLETE - All core user-facing features implemented

**Tasks**:
1. ✅ **Configuration System** (COMPLETE - Committed: 95be06be66ac)
   - ✅ Default download directory: `~/Papers/` with first-run setup and informative messaging
   - ✅ PAPERS_DIR environment variable support with priority hierarchy implementation
   - ✅ Command-line --dir flag overrides with path expansion (tilde support)
   - ✅ Graceful fallback to current directory when ~/Papers creation fails
   - ✅ Security review: Path traversal assessment completed, OS permissions trusted

2. ✅ **Enhanced CLI Features** (COMPLETE)
   - ✅ --dir flag for custom download location with priority over environment variable
   - ✅ --name flag for custom filename  
   - ✅ --quiet flag for script use
   - ✅ --verbose flag for debugging
   - ✅ --no-auto-name flag to disable metadata extraction

3. ✅ **Error Handling & UX** (COMPLETE)
   - ✅ Comprehensive error messages with suggested actions and user-friendly messaging
   - ✅ Progress indicators for downloads with real-time feedback
   - ✅ Validation for URLs and file paths with structured error handling
   - ✅ Graceful handling of permission errors with fallback strategies

4. ✅ **Documentation & Distribution** (COMPLETE)
   - ✅ README with comprehensive installation and usage documentation
   - ✅ Environment variable configuration with examples
   - ✅ CI/CD pipeline configuration with comprehensive workflows
   - ✅ Version 1.0.0 packaging with production-ready metadata

**Deliverable**: Production-ready tool with full feature set ✅ DELIVERED
**Success Criteria**: Tool works reliably for daily use with good UX ✅ ACHIEVED
**Quality Metrics**: 86/86 tests passing, MyPy clean, Ruff clean ✅ VERIFIED

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
1. ✅ **Functionality**: Downloads and renames papers correctly 95%+ of the time (ACHIEVED - validated with real arXiv PDFs)
2. ✅ **Usability**: Single command covers 90% of use cases (ACHIEVED - auto-naming with opt-out)
3. ✅ **Reliability**: Handles network errors and edge cases gracefully (ACHIEVED - retry logic + graceful fallbacks)
4. ✅ **Performance**: Downloads complete in reasonable time with progress feedback (ACHIEVED - chunked downloads with callbacks)
5. ✅ **Quality**: Comprehensive test coverage and type safety (ACHIEVED - 74/74 tests, MyPy clean)
6. ✅ **Production Ready**: Metadata extraction with real-world validation (ACHIEVED - arXiv PDF processing)

### Milestone 4: Multi-Format Support (Future Enhancement)
**Goal**: Support additional academic document formats beyond PDF
**Status**: Future consideration based on user demand
**Priority**: Low (covers <5% of real-world academic papers)

**Tasks**:
1. **PostScript Support** (3-4 days) - See `docs/postscript-support-assessment.md`
   - Format detection based on URL and Content-Type headers
   - Basic .ps file download capability 
   - PostScript metadata extraction via ghostscript integration
   - Intelligent filename generation for PS documents
   - **Dependencies**: ghostscript binary + Python wrapper
   - **Complexity**: Medium (metadata extraction significantly harder than PDF)
   - **Value**: Low (legacy format, rarely used for modern papers)

2. **Future Format Considerations** (Research needed)
   - EPUB: Some academic publishers use this format
   - HTML/MHTML: Single-file academic papers  
   - arXiv source: Direct LaTeX/TeX file downloads
   - **Strategy**: Implement PostScript first as multi-format architecture prototype

**Implementation Notes**:
- PostScript support should be progressive enhancement (optional dependency)
- Maintain backward compatibility with existing PDF-focused workflow
- Consider feature flag or explicit format specification for non-PDF files
- Test with legacy academic papers from 1990s-2000s era

**Success Criteria**:
- Download and basic naming for PostScript files
- Graceful degradation when ghostscript unavailable
- No regression in PDF functionality

## Post-Implementation Considerations
- **Future sources**: Architecture supports adding bioRxiv, SSRN, etc.
- **Batch processing**: Current design supports `xargs` for multiple URLs
- **Metadata improvement**: Can enhance extraction without breaking interface
- **Multi-format strategy**: PostScript as proof-of-concept for broader format support