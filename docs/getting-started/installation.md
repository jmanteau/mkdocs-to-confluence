# Installation

## Requirements

- Python 3.8 or higher
- MkDocs 1.1 or higher
- A Confluence instance with API access

## Install from PyPI

The recommended way to install mkdocs-to-confluence is via pip:

```bash
pip install mkdocs-to-confluence

```
Or add to your `requirements.txt`:

```
mkdocs>=1.1
mkdocs-to-confluence
```

## Install from Source

For development or to use the latest unreleased features:

```bash
git clone https://github.com/jmanteau/mkdocs-to-confluence.git
cd mkdocs-to-confluence
pip install -e .
```

## Verify Installation

Check that the plugin is installed correctly:

```bash
python -c "from mkdocs_to_confluence.plugin import MkdocsWithConfluence; print('✓ Installation successful')"
```

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with basic configuration
- [Configuration Reference](configuration.md) - Learn about all available options
