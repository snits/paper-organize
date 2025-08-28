# Contributors

## Project Creator & Maintainer

**Jerry Snitselaar** ([@jsnitsel](mailto:dev@snitselaar.org))
- Original concept and vision
- Project architecture and design decisions
- Core functionality implementation
- Quality standards and development workflow
- Release management and packaging
- Community governance and direction

## Core Contributors

**Claude (Anthropic)** - AI Collaborative Developer
- Exception hierarchy architecture and implementation
- Retry logic system with exponential backoff
- PDF metadata extraction engine (pypdf + pdf2doi integration)
- Comprehensive test suite design and implementation (74 tests)
- Type safety framework and MyPy compliance
- Code quality gates and SPDX license compliance
- Documentation structure and 1.0.0 release preparation
- Collaborative problem-solving and architectural refinement

## How to Contribute

We welcome contributions from the community! Here's how you can help:

### Types of Contributions

- **Bug Reports**: Found an issue? Please report it with detailed steps to reproduce
- **Feature Requests**: Have an idea? Open an issue to discuss it
- **Code Contributions**: Bug fixes, new features, performance improvements
- **Documentation**: Improve README, add examples, fix typos
- **Testing**: Add test cases, improve test coverage
- **Dependencies**: Update or optimize dependency usage

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone <your-fork-url>
   cd paper-dl
   ```

2. **Set Up Development Environment**
   ```bash
   uv sync --extra dev
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes**
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure SPDX license headers are present

5. **Quality Gates** (All must pass)
   ```bash
   # Run tests
   uv run pytest
   
   # Type checking
   uv run mypy src/ tests/
   
   # Linting
   uv run ruff check src/ tests/
   ```

6. **Commit Guidelines**
   - Use atomic commits (one logical change per commit)
   - Follow format: `component: brief description`
   - Include `Co-developed-by: Your Name <email>` in commit message
   
7. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure all CI checks pass

### Code Standards

- **Type Safety**: All code must have type annotations and pass MyPy
- **Testing**: New features require comprehensive test coverage
- **Documentation**: Public APIs must be documented
- **SPDX Compliance**: All source files need `SPDX-License-Identifier: MIT` header
- **Code Quality**: Must pass Ruff linting with project configuration

### Areas for Contribution

**Easy First Issues:**
- Documentation improvements
- Test case additions
- Error message improvements
- Example script creation

**Medium Complexity:**
- CLI option additions
- Progress bar enhancements
- Configuration file support
- Additional metadata sources

**Advanced:**
- Performance optimizations
- Concurrent downloads
- Plugin system architecture
- Alternative PDF libraries integration

### Code of Conduct

**Our Standards:**
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable Behavior:**
- Harassment, trolling, or insulting/derogatory comments
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

### Recognition

All contributors will be:
- Listed in this CONTRIBUTORS.md file
- Credited in release notes for their contributions
- Mentioned in commit messages with `Co-developed-by` trailers

### Questions and Support

- **General Questions**: Open a GitHub issue with the `question` label
- **Bug Reports**: Use the bug report template
- **Feature Discussions**: Open an issue with the `enhancement` label
- **Security Issues**: Email maintainer directly

### Project Governance

Currently maintained by Jerry Snitselaar. For major architectural changes:
1. Open an issue for discussion
2. Allow community feedback
3. Reach consensus before implementation

---

**Thank you for contributing to paper-dl!** 🚀

Every contribution, no matter how small, helps make this tool better for the academic community.