# Contributing

Thank you for your interest in contributing to mkdocs-to-confluence!

## Getting Started

### Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/mkdocs-to-confluence.git
cd mkdocs-to-confluence
```

### Set Up Development Environment

Using `uv` (recommended):

```bash
# Install uv if needed
pip install uv

# Set up environment
make py-setup

# Or manually:
uv venv
uv sync --group dev --group docs
```

### Install Pre-commit Hooks

```bash
make githooks-setup
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code in `src/mkdocs_to_confluence/`

### 3. Run Tests

```bash
make tests
```

### 4. Check Code Quality

```bash
# Lint and format
make lint-fix

# Type checking
make py-mypy

# All quality checks
make quality
```

### 5. Commit Changes

```bash
git add .
git commit -m "Add your feature"
```

Pre-commit hooks will run automatically.

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Maximum line length: 120 characters

### Linting

We use `ruff` for linting and formatting:

```bash
make py-ruff        # Check
make py-ruff-fix    # Fix automatically
```

### Type Checking

We use `mypy` for type checking:

```bash
make py-mypy
```

### Testing

We use `pytest` for testing:

```bash
make py-test        # Run all tests
make py-report      # Generate coverage report
```

## Testing

### Writing Tests

Tests are in `tests/` directory:

```python
def test_your_feature(config):
    """Test your feature."""
    plugin = MkdocsWithConfluence()
    plugin.config = config

    result = plugin.your_method()

    assert result == expected_value
```

### Test Fixtures

Use fixtures in `tests/fixtures/`:

- `configs.py` - Configuration fixtures
- `nav_data.py` - Navigation structures
- `markdown_samples.py` - Markdown content
- `confluence_responses.py` - Mock API responses

### Running Specific Tests

```bash
# Single test file
pytest tests/test_plugin.py

# Single test function
pytest tests/test_plugin.py::test_function_name

# With coverage
pytest --cov=mkdocs_to_confluence
```

### Integration Tests

Test dry-run functionality:

```bash
make test-dryrun
```

## Documentation

### Building Docs

```bash
make docs-build
```

### Serving Docs Locally

```bash
make docs-serve
```

Then open http://localhost:8000

### Documentation Style

- Use clear, concise language
- Include code examples
- Add configuration snippets
- Use admonitions for important notes

## Security

### Scanning

```bash
make py-security
```

Runs:
- `bandit` - Code security scanner
- `pip-audit` - Dependency vulnerability checker

### Reporting Issues

Report security issues privately to the maintainers.

## Release Process

(For maintainers)

### 1. Update Version

Edit `pyproject.toml`:

```toml
version = "0.6.0"
```

### 2. Update Changelog

Add new section to `CHANGELOG.md`:

```markdown
## [0.6.0] - 2025-XX-XX

### Added
- New feature description

### Fixed
- Bug fix description
```

### 3. Run Release Workflow

```bash
make release
```

This will:
- Show current version
- Prompt for new version
- Update files
- Run tests
- Build package
- Upload to TestPyPI

### 4. Test Installation

```bash
make test-install
```

### 5. Commit and Tag

```bash
make git-commit
make git-tag
```

### 6. Deploy to Production

```bash
make deploy-production
```

## Project Structure

```
mkdocs-to-confluence/
├── src/
│   └── mkdocs_to_confluence/
│       ├── __init__.py
│       ├── plugin.py           # Main plugin class
│       ├── exporter.py         # Dry-run exporter
│       └── _vendor/            # Vendored dependencies
├── tests/
│   ├── fixtures/               # Test fixtures
│   ├── test_plugin.py         # Plugin tests
│   └── test_exporter.py       # Exporter tests
├── docs/                       # Documentation
├── pyproject.toml             # Project configuration
├── Makefile                   # Development automation
└── README.md
```

## Getting Help

- Open an issue on GitHub
- Check existing issues and discussions
- Read the documentation
- Ask questions in PR comments

## Code of Conduct

Be respectful, inclusive, and collaborative.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
