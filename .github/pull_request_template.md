<!-- SPDX-License-Identifier: MIT -->
## Summary

Brief description of what this PR does and why.

## Type of Change

<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test coverage improvement

## Related Issues

<!-- Link to related issues -->
Fixes #(issue_number)
Related to #(issue_number)

## Changes Made

<!-- Detailed list of changes -->
- Added feature X to handle Y
- Fixed bug in metadata extraction
- Updated documentation for Z

## Testing

<!-- Describe the tests you ran -->
- [ ] All existing tests pass (`uv run pytest`)
- [ ] Type checking passes (`uv run mypy src/ tests/`)
- [ ] Linting passes (`uv run ruff check src/ tests/`)
- [ ] Added new tests for changed functionality
- [ ] Manual testing completed

### Test Commands
```bash
# Commands you ran to test this change
uv run pytest tests/test_new_feature.py -v
uv run paper-dl <test-url>
```

## Quality Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Added type hints for new code
- [ ] Added SPDX license headers to new files
- [ ] Updated documentation if needed
- [ ] Added tests for new functionality
- [ ] No decrease in test coverage

## Screenshots/Examples

<!-- If applicable, add screenshots or example output -->
```bash
# Example of new functionality
$ paper-dl https://arxiv.org/pdf/2301.00001.pdf --new-option
✓ Downloaded to: Smith_2023_Novel_Machine_Learning.pdf
```

## Breaking Changes

<!-- If this is a breaking change, describe what users need to do -->
None / Describe what users need to change

## Additional Notes

<!-- Any additional information for reviewers -->
- This change requires Python 3.9+ due to new syntax
- Performance improvement: 30% faster metadata extraction
- Backwards compatible with existing usage patterns