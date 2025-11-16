# MkDocs to Confluence

**MkDocs plugin for converting and uploading Markdown pages to Confluence**

[![PyPI version](https://badge.fury.io/py/mkdocs-to-confluence.svg)](https://badge.fury.io/py/mkdocs-to-confluence)
[![Python Support](https://img.shields.io/pypi/pyversions/mkdocs-to-confluence.svg)](https://pypi.org/project/mkdocs-to-confluence/)
[![License](https://img.shields.io/pypi/l/mkdocs-to-confluence.svg)](https://github.com/jmanteau/mkdocs-to-confluence/blob/main/LICENSE)

Automatically publish your MkDocs documentation to Atlassian Confluence during builds. Convert Markdown to Confluence format and maintain synchronized documentation across platforms.

## Features

### Core Capabilities
- **Automated Publishing** - Seamlessly publish MkDocs documentation to Confluence during builds
- **Unlimited Hierarchy Depth** - Support for arbitrary nesting levels
- **Smart Updates** - Creates new pages or updates existing ones based on title matching
- **Intelligent Update Detection** - Compares content before updating to skip unnecessary changes, reducing version bumps
- **Orphaned Page Management** - Automatically detects and optionally cleans up pages that no longer exist in your documentation, keeping your Confluence space in perfect sync
- **Image Management** - Automatically uploads and updates images as attachments with SHA1 hash-based change detection

### Authentication & Security
- **Multiple Authentication Methods** - Supports Basic Auth, API tokens, and OAuth Bearer tokens
- **Environment Variable Support** - Secure credential management for CI/CD pipelines

### Developer Experience
- **Dry Run Mode** - Export to filesystem for review before publishing to Confluence
- **Conditional Publishing** - Enable/disable based on environment variables
- **Enhanced Markdown** - Extended syntax support including strikethrough, admonitions, task lists, and more
- **Comprehensive Logging** - Verbose and debug modes with detailed content comparison

## Documentation Structure

This documentation follows the **[Diátaxis](https://diataxis.fr/)** framework, organizing content by purpose:

### 📚 Tutorials (Learning-Oriented)

**For newcomers who want to learn by doing**

Start here if you're new to mkdocs-to-confluence. Tutorials guide you step-by-step through your first setup and configuration.

- [Installation](getting-started/installation.md) - Install the plugin
- [Quick Start](getting-started/quick-start.md) - Your first Confluence sync
- [Configuration](getting-started/configuration.md) - Configure the plugin

### 🛠️ How-To Guides (Task-Oriented)

**For users who need to accomplish specific tasks**

Practical guides for solving real-world problems and implementing specific features.

- [Basic Usage](user-guide/basic-usage.md) - Publishing workflow
- [Advanced Features](user-guide/advanced-features.md) - H1 stripping, custom settings
- [Managing Orphaned Pages](user-guide/managing-orphaned-pages.md) - Sync your Confluence space
- [Dry Run Mode](user-guide/dry-run.md) - Test before publishing
- [GitHub Pages Deployment](user-guide/github-pages-deployment.md) - Deploy to GitHub Pages
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Contributing](contributing.md) - How to contribute

### 📖 Reference (Information-Oriented)

**For users who need precise technical information**

Complete technical specifications and API documentation.

- [Configuration Options](reference/configuration.md) - Complete config reference
- [API Reference](reference/SUMMARY.md) - Python API documentation
- [Markdown Showcase](markdown-showcase.md) - Supported Markdown features

### 💡 Explanation (Understanding-Oriented)

**For users who want to understand how things work**

Conceptual guides explaining the architecture, design decisions, and key concepts.

- [How It Works](explanation/architecture.md) - Plugin architecture and sync process
- [Key Concepts](explanation/concepts.md) - Pages, hierarchy, and content management

## Quick Start

```bash
# Install
pip install mkdocs-to-confluence

# Configure mkdocs.yml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: YOUR_SPACE
      parent_page_name: Documentation

# Publish
mkdocs build
```

Your documentation is now synced to Confluence! 🎉

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/jmanteau/mkdocs-to-confluence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jmanteau/mkdocs-to-confluence/discussions)
- **Changelog**: [Release Notes](changelog.md)

## License

MIT License - see [LICENSE](https://github.com/jmanteau/mkdocs-to-confluence/blob/main/LICENSE) for details.
