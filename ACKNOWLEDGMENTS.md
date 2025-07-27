# Acknowledgments

paper-dl is built on the shoulders of giants. We gratefully acknowledge the following open-source projects and their contributors:

## Core Runtime Dependencies

### [pypdf](https://github.com/py-pdf/pypdf) 
- **License**: BSD-3-Clause
- **Purpose**: Pure Python PDF library for metadata extraction
- **Maintainer**: Martin Thoma and the py-pdf team
- **Why we use it**: Reliable PDF parsing and metadata extraction without external dependencies

### [pdf2doi](https://github.com/MicheleCotrufo/pdf2doi)
- **License**: MIT 
- **Purpose**: Academic paper identifier extraction (DOI, arXiv ID)
- **Maintainer**: Michele Cotrufo
- **Why we use it**: Specialized extraction of academic identifiers from PDF content

### [Click](https://github.com/pallets/click)
- **License**: BSD-3-Clause
- **Purpose**: Command-line interface framework
- **Maintainer**: Pallets team
- **Why we use it**: Elegant CLI with automatic help generation and parameter validation

### [Requests](https://github.com/psf/requests)
- **License**: Apache-2.0
- **Purpose**: HTTP library for file downloads
- **Maintainer**: Kenneth Reitz and the Requests team
- **Why we use it**: Reliable HTTP downloads with excellent error handling

### [tqdm](https://github.com/tqdm/tqdm)
- **License**: MIT/MPL-2.0
- **Purpose**: Progress bar library
- **Maintainer**: Casper da Costa-Luis and contributors
- **Why we use it**: User-friendly progress indication during downloads

## Development and Quality Assurance

### [pytest](https://github.com/pytest-dev/pytest)
- **License**: MIT
- **Purpose**: Testing framework
- **Why we use it**: Comprehensive test suite with 74 tests ensuring reliability

### [MyPy](https://github.com/python/mypy)
- **License**: MIT  
- **Purpose**: Static type checker
- **Why we use it**: Type safety and early error detection

### [Ruff](https://github.com/astral-sh/ruff)
- **License**: MIT
- **Purpose**: Fast Python linter and formatter
- **Why we use it**: Code quality and consistent formatting

## Special Thanks

- **Michele Cotrufo** for creating pdf2doi, which makes academic metadata extraction possible
- **Martin Thoma** for maintaining pypdf and providing reliable PDF processing
- **Claude (Anthropic)** for collaborative development, architectural design, and comprehensive implementation of core features
- **The entire Python packaging ecosystem** for tools like uv, setuptools, and PyPI
- **httpbin.org** for providing reliable HTTP endpoints for integration testing

## License Compatibility

All dependencies use licenses that are compatible with our MIT license:
- MIT ✓ (same license)
- BSD-3-Clause ✓ (permissive, compatible) 
- Apache-2.0 ✓ (permissive, compatible)
- MPL-2.0 ✓ (permissive, compatible)

## Contributing Back

We believe in giving back to the open-source community. If you encounter issues with our dependencies while using paper-dl, please consider:
1. Reporting bugs to the upstream projects
2. Contributing fixes when possible
3. Supporting maintainers through donations or sponsorships

---

*This project stands on the foundation built by countless open-source contributors. Thank you.*