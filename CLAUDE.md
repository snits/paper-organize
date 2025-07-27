# Tooling
- The project is managed with `uv`.
- The following tools are available for searching beyond the typical linux tools: rg, vgrep, fd, fzf, bat, and exa.
- mypy, and ruff are to be used for type hinting, and linting as part of the quality gating process.

# Testing
- Testing is run with pytest through uv `uv run pytest`

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
