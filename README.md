# mkdocs-to-confluence

[![PyPI](https://img.shields.io/pypi/v/mkdocs-to-confluence)](https://pypi.org/project/mkdocs-to-confluence/) [![Python Version](https://img.shields.io/pypi/pyversions/mkdocs-to-confluence)](https://pypi.org/project/mkdocs-to-confluence/) [![License](https://img.shields.io/pypi/l/mkdocs-to-confluence)](https://github.com/jmanteau/mkdocs-to-confluence/blob/main/LICENSE) [![Downloads](https://img.shields.io/pypi/dm/mkdocs-to-confluence)](https://pypi.org/project/mkdocs-to-confluence/)

A MkDocs plugin that automatically publishes your documentation to Atlassian Confluence. Convert Markdown pages to Confluence format and maintain synchronized documentation across platforms.

---

**[Full Documentation](https://jmanteau.github.io/mkdocs-to-confluence/) following Diataxis framework with :**
  * [Tutorials (Learning-Oriented)](https://jmanteau.github.io/mkdocs-to-confluence/getting-started/installation/)
  * [How-To Guides (Task-Oriented)](https://jmanteau.github.io/mkdocs-to-confluence/user-guide/basic-usage/)
  * [Reference (Information-Oriented)](https://jmanteau.github.io/mkdocs-to-confluence/reference/configuration/)
  * [Explanation (Understanding-Oriented)](https://jmanteau.github.io/mkdocs-to-confluence/explanation/architecture/)

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Markdown Support](#markdown-support)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)


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


## Installation

### Install from PyPI

The recommended way to install mkdocs-to-confluence is via pip:

```bash
pip install mkdocs-to-confluence

```
Or add to your `requirements.txt`:

```
mkdocs>=1.1
mkdocs-to-confluence
```


## Quick Start

### API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a name and copy the token

### Space Key

Find your Confluence space key:
1. Go to your Confluence space
2. Click "Space Settings"
3. The space key is shown in the URL: `https://your-domain.atlassian.net/wiki/spaces/SPACEKEY/`


## Configuration

Open your `mkdocs.yml` and add the plugin:

```yaml
plugins:
  - search  # Keep your existing plugins
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: YOUR_SPACE
      parent_page_name: Documentation
```


Set up your Confluence credentials using environment variables (recommended):

```bash
export JIRA_USERNAME=your-email@example.com
export CONFLUENCE_API_TOKEN=your-api-token
```

!!! tip "Getting Your API Token"
    Generate an API token at [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)

Alternatively, you can specify credentials directly in `mkdocs.yml` (not recommended for production):

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      username: your-email@example.com
      api_token: your-token  # Better to use environment variable!
```

### Orphaned Page Management

Keep your Confluence space in sync by automatically detecting and optionally cleaning up pages that no longer exist in your documentation:

```yaml
plugins:
  - mkdocs-to-confluence:
      # ... other config ...
      cleanup_orphaned_pages: false  # Set to true to auto-delete orphaned pages
      keep_pages:  # Pages to preserve even if not in docs
        - "Archive"
        - "Manual Documentation"
      page_label: auto-generated-docs  # Label all synced pages for easy filtering
```

**How it works:**
- Always warns about orphaned pages (pages in Confluence but not in your docs)
- Optionally deletes them automatically when `cleanup_orphaned_pages: true`
- Preserves pages listed in `keep_pages` to protect manual content
- See [Managing Orphaned Pages](https://jmanteau.github.io/mkdocs-to-confluence/user-guide/managing-orphaned-pages/) for detailed strategies

For complete configuration options, see the [Configuration Reference](https://jmanteau.github.io/mkdocs-to-confluence/reference/configuration/).



## Markdown Support

See the [Markdown Showcase](docs/markdown-showcase.md) and [full documentation](https://jmanteau.github.io/mkdocs-to-confluence/).



## Troubleshooting

### Common Issues

For detailed troubleshooting, see the [full documentation](https://jmanteau.github.io/mkdocs-to-confluence/troubleshooting/).

**Quick fixes:**
- **Authentication failed**: Verify username and API token
- **Space not found**: Check space key (case-sensitive)
- **Parent page not found**: Create parent page in Confluence first
- **Images not uploading**: Check image paths in Markdown

**Debug mode:**

```yaml
plugins:
  - mkdocs-to-confluence:
      debug: true        # General debugging (API calls, operations)
      debug_diff: true   # Content comparison details (creates temp files)
      verbose: true
```

**Dry run testing:**

```yaml
plugins:
  - mkdocs-to-confluence:
      dryrun: true
      export_dir: confluence-export
```


## Requirements

- **Python**: >=3.8
- **MkDocs**: >=1.1
- **Dependencies**: jinja2, requests, mistune>=3.1.2, mime>=0.1.0


## Contributing

Contributions are welcome! See the [Contributing Guide](https://jmanteau.github.io/mkdocs-to-confluence/contributing/) for details.

**Quick start:**

```bash
git clone https://github.com/jmanteau/mkdocs-to-confluence.git
cd mkdocs-to-confluence
make py-setup
make py-test
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

This project includes a vendored copy of [md2cf](https://github.com/andrust/md2cf) (MIT License), which has been modified to support mistune 3.x and additional Confluence features.


## Acknowledgments

- Original [mkdocs-with-confluence](https://github.com/pawelsikora/mkdocs-with-confluence/) by Paweł Sikora
- Original [md2cf](https://github.com/hugovk/md2cf) by Giacomo Gaino
- Enhanced md2cf fork by [andrust](https://github.com/andrust/md2cf) with mistune 3.x support
- [MkDocs](https://www.mkdocs.org/) documentation framework


## Support

- **Documentation**: [https://jmanteau.github.io/mkdocs-to-confluence/](https://jmanteau.github.io/mkdocs-to-confluence/)
- **Issues**: [GitHub Issues](https://github.com/jmanteau/mkdocs-to-confluence/issues)

---

**This README is auto-generated from documentation sources. Do not edit directly.**
**To update, modify the docs and run `make readme`**