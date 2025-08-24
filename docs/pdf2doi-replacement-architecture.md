# ABOUTME: Architecture design for replacing AGPL-licensed pdf2doi dependency
# ABOUTME: Comprehensive plan for MIT-licensed metadata extraction pipeline

# PDF2DOI Replacement Architecture

## Executive Summary

This document outlines the architecture for replacing the AGPL-licensed `pdf2doi` dependency with MIT-licensed alternatives to ensure clean license compliance while maintaining and improving functionality.

## Current Architecture Problems

### License Contamination
- **pdf2doi** (AGPL-3.0) → **pymupdf** (AGPL-3.0) 
- Contaminates MIT-licensed project
- Blocks commercial usage and redistribution

### Functional Limitations
- Black box DOI/arXiv extraction
- Unreliable PDF text parsing for arXiv papers
- Limited error handling and fallback options
- No caching or performance optimization

## Proposed Architecture

### New Metadata Extraction Pipeline

```
PDF Input →
├── PyPDF (basic metadata: title, author, dates)
├── Enhanced Text Extraction (pdfplumber)
├── Pattern Detection (regex for DOI/arXiv patterns)  
├── External API Enrichment (arxiv.py + CrossRef)
└── Consolidated Metadata Output
```

### MIT-Licensed Replacement Strategy

1. **arXiv Papers**: Direct API access via `arxiv.py` (MIT)
   - More reliable than PDF text parsing
   - Rich metadata: title, authors, year, abstract
   - Handles all arXiv URL formats and ID patterns

2. **DOI Papers**: Enhanced text extraction + CrossRef API
   - `pdfplumber` (MIT) for superior PDF text extraction
   - Regex patterns for DOI identification
   - CrossRef REST API for validation and metadata

### New Dependencies (All MIT Licensed)
```toml
dependencies = [
    "pdfplumber>=0.9.0",  # Enhanced PDF text extraction
    "arxiv>=2.1.0",       # Official arXiv API client
    # Existing dependencies remain unchanged
    "click>=8.0.0",
    "requests>=2.25.0", 
    "pypdf>=4.0.0",
    "tqdm>=4.60.0",
]
```

## Module Architecture

### New Module Structure
```
src/paperorganize/
├── metadata_extraction/
│   ├── __init__.py              # Public interfaces
│   ├── text_extractors.py      # PDF text extraction strategies
│   ├── pattern_matchers.py     # DOI/arXiv regex patterns
│   ├── api_clients.py          # arXiv & CrossRef API clients
│   └── metadata_enricher.py    # Orchestration and enrichment logic
└── metadata.py (updated)       # Main interface - transparent replacement
```

### Component Design

#### 1. Text Extractors (`text_extractors.py`)
```python
class PDFTextExtractor(Protocol):
    def extract_text(self, pdf_path: str) -> str: ...

class PdfPlumberExtractor:
    """Enhanced text extraction with layout preservation."""
    def extract_text(self, pdf_path: str) -> str:
        # Better handling of multi-column layouts, tables
        # Preserves text structure for pattern matching
        
class PyPDFExtractor:
    """Fallback text extraction using existing pypdf."""
    def extract_text(self, pdf_path: str) -> str:
        # Existing reliable extraction as backup
```

#### 2. Pattern Matchers (`pattern_matchers.py`)
```python
@dataclass
class IdentifierMatch:
    identifier: str
    identifier_type: str  # "doi" | "arxiv"
    confidence: float

def find_doi_patterns(text: str) -> List[IdentifierMatch]:
    """Find DOI patterns with confidence scoring."""
    # Patterns:
    # - 10.1000/123456 (standard format)
    # - doi: 10.1000/123456 (prefixed)
    # - https://doi.org/10.1000/123456 (URL format)
    
def find_arxiv_patterns(text: str) -> List[IdentifierMatch]:
    """Find arXiv ID patterns with confidence scoring."""
    # Patterns:
    # - arXiv:1234.5678v1 (new format)
    # - cond-mat/0123456 (old format) 
    # - https://arxiv.org/abs/1234.5678 (URL format)
```

#### 3. API Clients (`api_clients.py`)
```python
class ArxivClient:
    """Official arXiv API client with caching."""
    def get_metadata(self, arxiv_id: str) -> dict:
        # Uses arxiv.py library
        # Returns: title, authors, year, abstract, categories
        
class CrossRefClient:
    """CrossRef REST API client with rate limiting."""  
    def get_metadata(self, doi: str) -> dict:
        # Validates DOI and retrieves rich metadata
        # Handles rate limiting, retries, caching
```

#### 4. Metadata Enricher (`metadata_enricher.py`)
```python
class EnhancedMetadataExtractor:
    """Orchestrates the complete extraction pipeline."""
    
    def extract_identifiers_and_enrich(self, pdf_path: str, metadata: PaperMetadata) -> None:
        # 1. Extract text using fallback chain
        # 2. Find patterns with confidence scoring
        # 3. Validate via appropriate API
        # 4. Merge with existing pypdf metadata
```

## Integration Points

### Metadata Pipeline Integration
- **metadata.py**: Replace `_extract_with_pdf2doi()` with `_extract_with_enhanced_pipeline()`
- **processors.py**: No changes needed - uses metadata.py interface
- **CLI**: No changes needed - transparent replacement

### Backward Compatibility
- Same `PaperMetadata` dataclass interface
- Same `extract_pdf_metadata()` function signature  
- Same CLI behavior and options
- Same filename generation logic

## Error Handling Strategy

### Graceful Degradation
- **Network Issues**: Fall back to pypdf-only metadata
- **API Failures**: Continue with basic PDF extraction
- **Malformed PDFs**: Multiple text extractor fallbacks

### Resilience Features
- **Retry Logic**: Exponential backoff for API calls
- **Timeout Handling**: Prevent hanging on slow PDFs
- **Caching**: HTTP cache for API responses
- **Logging**: Debug-level pattern matching and API logs

## Performance Considerations

### Optimizations
- **Early Exit**: Stop text extraction once identifier found
- **Text Limits**: Process first 5 pages only for large PDFs
- **Concurrent APIs**: Parallel API calls for batch processing
- **Response Caching**: Cache API responses using requests-cache

### Performance Comparison
- **arXiv Papers**: Direct API ≫ PDF text parsing (faster + more reliable)
- **DOI Papers**: pdfplumber text extraction ≈ pdf2doi (similar speed, better accuracy)
- **Network Overhead**: API calls add latency but provide much richer metadata

## Migration Strategy

### Atomic Commit Sequence (5 commits)

#### Commit 1: Foundation Setup
- Add new MIT dependencies to pyproject.toml
- Create metadata_extraction module structure
- Add protocol definitions and interfaces
- **Working State**: Existing functionality unchanged, new infrastructure ready

#### Commit 2: Core Extraction Implementation  
- Implement text extractors (pdfplumber + pypdf fallback)
- Implement pattern matchers with comprehensive regex
- Add unit tests with real PDF samples
- **Working State**: New extraction components ready, old system still active

#### Commit 3: API Integration
- Implement ArxivClient using arxiv.py library
- Implement CrossRefClient using CrossRef REST API
- Add MetadataEnricher orchestration layer  
- **Working State**: Complete new pipeline implemented, old system still active

#### Commit 4: Pipeline Integration
- Replace _extract_with_pdf2doi() with new pipeline
- Update metadata.py to use enhanced extraction
- Add integration tests proving feature parity
- **Working State**: New pipeline active, old dependencies still present for safety

#### Commit 5: AGPL Cleanup
- Remove pdf2doi from dependencies
- Remove old pdf2doi extraction code
- Update compliance documentation
- **Working State**: Clean MIT-only codebase, full functionality preserved

### Risk Mitigation
- **Working States**: Each commit leaves system fully functional
- **Rollback Capability**: Can revert any single commit safely  
- **Feature Parity Testing**: Comprehensive tests ensure no functionality loss
- **Gradual Migration**: Old system remains until new system proven

## Benefits of New Architecture

### License Compliance
- ✅ **Pure MIT**: No AGPL contamination
- ✅ **Commercial Use**: Enables commercial distribution
- ✅ **Clear Dependencies**: All dependencies well-documented and compatible

### Functional Improvements  
- 🚀 **Better arXiv Handling**: Direct API vs unreliable PDF parsing
- 🚀 **Enhanced DOI Extraction**: pdfplumber handles complex layouts better
- 🚀 **Robust Error Handling**: Graceful fallbacks, better logging
- 🚀 **Performance Optimized**: Caching, early exit, concurrent processing

### Architectural Benefits
- 🔧 **Extensible Design**: Easy to add new identifier types or APIs
- 🔧 **Testable Components**: Clear interfaces, mockable dependencies  
- 🔧 **Maintainable Code**: Well-structured, documented, type-hinted
- 🔧 **Future-Proof**: Standards-compliant API usage, not screen-scraping

## Testing Strategy

### Unit Tests
- Text extractors with various PDF layouts
- Pattern matchers with comprehensive identifier formats
- API clients with mock responses and error conditions
- Metadata enricher with different data combinations

### Integration Tests  
- End-to-end pipeline with real PDF samples
- Feature parity tests comparing old vs new extraction
- Error handling tests with network failures
- Performance tests with large batch processing

### Validation Tests
- Real arXiv papers with known metadata
- Real DOI papers with known metadata  
- Edge cases: malformed PDFs, network issues
- Regression tests ensuring no functionality loss

## Conclusion

This architecture completely eliminates AGPL license contamination while improving functionality and maintainability. The gradual migration strategy ensures zero downtime and full backward compatibility, while the enhanced extraction pipeline provides more reliable and richer metadata extraction capabilities.

The investment in replacing pdf2doi pays dividends in:
- **Legal Compliance**: Clean MIT licensing for commercial use
- **Technical Quality**: More robust and extensible architecture
- **User Experience**: Better metadata extraction, especially for arXiv papers  
- **Maintenance**: Well-tested, documented, and maintainable codebase