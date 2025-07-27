# ABOUTME: Technical assessment for adding PostScript document support to paper-dl
# ABOUTME: Analyzes feasibility, implementation challenges, and effort estimates

# PostScript Support Assessment

## Executive Summary

Adding PostScript (.ps) support to paper-dl is **technically feasible** but offers **limited practical value**. While basic download functionality would be straightforward, intelligent metadata extraction and auto-naming would be significantly more complex than PDF support.

**Recommendation**: Implement as a low-priority enhancement if time permits, but PDF support covers 95%+ of real-world academic papers.

## Current Architecture Analysis

### What Works Immediately ✅
- **Download functionality**: Already format-agnostic, no changes needed
- **Directory management**: PAPERS_DIR and --dir flags work with any file type
- **Basic file handling**: Network resilience and retry logic apply universally

### What Requires Changes

#### 1. File Extension Handling (Easy - 1-2 hours)
**Current limitation**: `src/paperdl/cli.py:116-121` hardcodes `.pdf` extension
```python
if not filename or not filename.endswith(".pdf"):
    filename = "paper.pdf"
```

**Solution**: Format detection based on URL and Content-Type headers
```python
def determine_format(url: str, content_type: str) -> tuple[str, str]:
    """Returns (extension, default_filename)"""
    if url.endswith('.ps') or 'postscript' in content_type:
        return 'ps', 'paper.ps'
    return 'pdf', 'paper.pdf'
```

#### 2. Metadata Extraction (Medium-Hard - 1-2 days)
**Current system**: PDF-specific libraries
- `PyPDF2.PdfReader` for document metadata
- `pdf2doi` for DOI/arXiv ID extraction

**PostScript challenges**:
- Less structured format than PDF
- No equivalent to `pdf2doi` for academic paper detection
- Would need `ghostscript` dependency for reliable parsing

**Potential approach**:
```python
def extract_ps_metadata(ps_path: Path) -> PaperMetadata:
    """Extract metadata from PostScript file using ghostscript."""
    # Use ghostscript to extract document info dictionary
    # Parse PS header comments (%%Title, %%Creator, etc.)
    # Extract creation date from PS structure
    # Limited compared to PDF metadata richness
```

#### 3. Auto-Naming Logic (Medium - 1 day)
**Required changes**:
- Format-aware metadata extraction dispatcher
- Graceful degradation when PS metadata is sparse
- Maintain existing PDF behavior as default

## Technical Implementation Plan

### Phase 1: Basic PostScript Download (Low effort)
- Add format detection logic
- Support `.ps` file extensions
- Maintain existing PDF behavior as default
- **Effort**: 2-4 hours

### Phase 2: PostScript Metadata Extraction (Medium effort)  
- Add `ghostscript` dependency (via `python-ghostscript` or subprocess)
- Implement PS header parsing for basic metadata
- Handle cases where metadata is unavailable
- **Effort**: 1-2 days

### Phase 3: Integration and Testing (Medium effort)
- Update test suite for dual format support
- Add integration tests with real PS files
- Update documentation and help text
- **Effort**: 1 day

## Technical Challenges

### 1. PostScript Structure Limitations
- **PDFs**: Structured format with standardized metadata fields
- **PostScript**: Procedural language with optional metadata comments
- **Impact**: Less reliable metadata extraction

### 2. Academic Paper Distribution Reality
- **Modern papers**: 95%+ distributed as PDF
- **PostScript usage**: Mostly legacy documents from 1990s-2000s
- **Impact**: Low practical value for target use case

### 3. Dependency Complexity
- **Current**: Pure Python with optional PDF libraries
- **With PS**: Requires `ghostscript` binary + Python wrapper
- **Impact**: Increased installation complexity

### 4. Metadata Quality Gap
- **PDF**: Rich metadata + DOI extraction via `pdf2doi`
- **PostScript**: Basic metadata only, no DOI/arXiv detection
- **Impact**: Reduced auto-naming intelligence for PS files

## Dependencies Required

```toml
# pyproject.toml additions for PostScript support
[project.optional-dependencies]
postscript = [
    "ghostscript>=0.7",  # Python wrapper for ghostscript
]
```

**System requirement**: `ghostscript` binary must be installed

## Testing Strategy

### Unit Tests
- Format detection logic
- PostScript metadata extraction (with mock files)
- Filename generation with PS metadata

### Integration Tests  
- Download real PostScript files from test endpoints
- End-to-end CLI testing with `.ps` URLs
- Error handling for corrupted PS files

### Test Files Needed
- Sample academic papers in PostScript format
- PS files with various metadata completeness levels
- Malformed PS files for error testing

## Migration Considerations

### Backward Compatibility
- **Guaranteed**: All existing PDF functionality unchanged
- **CLI behavior**: Maintains current defaults
- **Configuration**: No breaking changes to existing options

### Progressive Enhancement
- PS support could be opt-in initially
- Feature flag: `--format ps` or auto-detection
- Graceful degradation when ghostscript unavailable

## Effort Summary

| Component | Complexity | Effort | Dependencies |
|-----------|------------|--------|--------------|
| Basic PS download | Low | 2-4 hours | None |
| Metadata extraction | Medium-High | 1-2 days | ghostscript |
| Testing & integration | Medium | 1 day | Test PS files |
| **Total** | **Medium** | **3-4 days** | **ghostscript** |

## Recommendation

**Priority**: Low (nice-to-have)

**Rationale**:
1. **Limited practical value**: Modern academic papers are distributed as PDF
2. **Complexity vs. benefit**: Significant effort for minimal user impact  
3. **Maintenance burden**: Additional dependency and edge cases
4. **Alternative**: Users can convert PS→PDF with existing tools

**If implemented**: 
- Start with basic download support only
- Add metadata extraction if user demand justifies effort
- Consider making ghostscript dependency optional with graceful degradation

## Future Considerations

Other format extensions that might provide more value:
- **EPUB**: Some academic publishers use this format
- **HTML**: Single-file academic papers (MHTML)
- **arXiv source**: Direct LaTeX/TeX file downloads

PostScript support could serve as a prototype for a general "multi-format academic document downloader" architecture.