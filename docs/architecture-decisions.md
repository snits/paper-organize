# ABOUTME: Architectural decision records for paper-organize unified tool design
# ABOUTME: Documents key design choices, rationale, and trade-offs for major decisions

# Architecture Decision Records

## ADR-001: Unified Tool Strategy Pattern Architecture

**Date**: 2025-01-27  
**Status**: Implemented  
**Context**: Original paper-dl tool only supported URL downloads. User requested support for organizing existing PDF files and directories.

### Decision
Implement a unified tool using the Strategy Pattern with smart input detection rather than separate tools or mode flags.

**Architecture Components**:
- **Input Detection**: Smart type detection (URL vs file vs directory) with comprehensive validation
- **Strategy Pattern**: URLProcessor, FileProcessor, DirectoryProcessor with shared interface
- **Shared Utilities**: DRY-compliant metadata naming used across all processors
- **Unified CLI**: Single INPUT argument with automatic processor selection

### Expert Consultation Process
- **UX Expert**: Initially recommended separate tools, later agreed unified approach after package rename consideration
- **Systems Architect**: Recommended unified tool for maintainability from the start
- **Code-Reviewer**: Enforced atomic commit discipline and architecture quality standards

### Rationale
1. **Maintainability**: Single codebase vs multiple tools reduces maintenance burden
2. **User Experience**: Unified interface eliminates mode confusion and command proliferation
3. **Extensibility**: Strategy pattern enables easy addition of new input types (e.g., web scraping)
4. **Code Quality**: Shared utilities eliminate duplication while maintaining clean separation

### Trade-offs
**Benefits**:
- Single command interface covers all use cases
- Consistent error handling and user feedback
- Shared metadata processing logic (DRY compliance)
- Easy extensibility for new input types

**Costs**:
- Slightly more complex than URL-only tool
- Input detection adds small validation overhead
- Larger binary size vs focused single-purpose tool

### Implementation Details
```python
# Strategy interface
class ProcessorProtocol(Protocol):
    def process(self, input_arg: str, destination_dir: Path, 
               custom_name: str | None, *, auto_name: bool, quiet: bool) -> list[ProcessingResult]

# Processors implement consistent interface
class URLProcessor: ...
class FileProcessor: ...  
class DirectoryProcessor: ...

# Smart input detection
def detect_input_type(input_arg: str) -> InputType
```

**Quality Metrics**: 114/114 tests passing, full MyPy compliance, enhanced Ruff configuration

---

## ADR-002: Package Rename Strategy

**Date**: 2025-01-27  
**Status**: Implemented  
**Context**: UX expert initially objected to unified tool due to misleading "paper-dl" name.

### Decision
Rename package from "paper-dl" to "paper-organize" to reflect unified organize/download capabilities.

### Rationale
1. **Truth in Advertising**: Name accurately describes all tool capabilities
2. **User Expectations**: "organize" clearly includes both download and file management
3. **UX Alignment**: Resolved UX expert's concerns about misleading naming
4. **Future Flexibility**: Name supports additional organization features

### Implementation Approach
- Atomic commit with comprehensive package structure update
- All imports, build system, and documentation updated consistently
- Backward compatibility maintained for existing URL workflow

---

## ADR-003: Shared Metadata Utilities Design

**Date**: 2025-01-27  
**Status**: Implemented  
**Context**: Initial implementation had duplicated metadata naming logic in URLProcessor and FileProcessor.

### Decision
Extract shared metadata processing into dedicated `metadata_naming.py` module.

### Rationale
1. **DRY Compliance**: Eliminate code duplication across processors
2. **Consistency**: Ensure identical naming behavior across all input types
3. **Maintainability**: Single source of truth for metadata processing logic
4. **Testability**: Isolated testing of shared functionality

### Implementation
```python
# Shared utility function
def apply_metadata_naming(file_path: Path, *, quiet: bool) -> Path:
    """Apply metadata-based naming to PDF file. Used by all processors."""
```

**Quality Impact**: Resolved code-reviewer DRY violation feedback, improved test coverage

---

## ADR-004: Atomic Commit Discipline

**Date**: 2025-01-27  
**Status**: Implemented  
**Context**: Code-reviewer rejected initial massive commit violating atomic commit principles.

### Decision
Break large unified tool implementation into 6 logical atomic commits following Linux kernel standards.

**Commit Sequence**:
1. `refactor: rename package from paperdl to paperorganize`
2. `feat: add input type detection for URLs, files, and directories`
3. `feat: add processor strategy pattern for unified input handling`
4. `feat: integrate unified input processing in CLI interface`
5. `docs: update documentation and dependencies for unified functionality`
6. `style: add missing newline at end of CLI file`

### Rationale
1. **Bisectability**: Each commit leaves codebase in working state
2. **Logical Boundaries**: Single functional change per commit
3. **Review Quality**: Smaller changes enable better code review
4. **Git History**: Clear narrative of feature development progression

### Quality Benefits
- Easier debugging through precise change identification
- Selective reverting of specific functionality
- Better collaboration through understandable change units
- Clean development story in git history

---

## ADR-005: Keyword-Only Parameter Design

**Date**: 2025-01-27  
**Status**: Implemented  
**Context**: Code-reviewer identified FBT violations with boolean positional parameters.

### Decision
Use keyword-only parameters for boolean flags with `*, auto_name: bool, quiet: bool` syntax.

### Rationale
1. **API Clarity**: Explicit flag names prevent boolean parameter confusion
2. **Linting Compliance**: Eliminates FBT (flake8-boolean-trap) violations
3. **Maintainability**: Self-documenting function calls
4. **Type Safety**: Improved function signature expressiveness

### Implementation Pattern
```python
def process(self, input_arg: str, destination_dir: Path, 
           custom_name: str | None, *, auto_name: bool, quiet: bool) -> list[ProcessingResult]
```

**Quality Impact**: Enhanced API design with better call site readability

---

## Future Architecture Considerations

### Extensibility Patterns
- **New Input Types**: Strategy pattern enables web scraping, API integration
- **Output Formats**: Processing results support multiple destination strategies  
- **Metadata Sources**: Layered extraction strategy supports additional providers

### Performance Optimization Opportunities
- **Concurrent Processing**: Directory processor could parallelize file operations
- **Streaming Downloads**: Chunked processing for large files
- **Caching Strategy**: Metadata extraction results for repeated operations

### Monitoring and Observability
- **Processing Metrics**: Success rates, processing times, error patterns
- **User Analytics**: Input type distributions, feature usage patterns
- **Quality Metrics**: Automated testing coverage, performance benchmarks