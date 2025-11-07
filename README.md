# mkdocs-to-confluence

[![PyPI](https://img.shields.io/pypi/v/mkdocs-to-confluence)](https://pypi.org/project/mkdocs-to-confluence/)
[![Python Version](https://img.shields.io/pypi/pyversions/mkdocs-to-confluence)](https://pypi.org/project/mkdocs-to-confluence/)
[![License](https://img.shields.io/pypi/l/mkdocs-to-confluence)](https://github.com/jmanteau/mkdocs-to-confluence/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/mkdocs-to-confluence)](https://pypi.org/project/mkdocs-to-confluence/)

A MkDocs plugin that automatically publishes your documentation to Atlassian Confluence. Convert Markdown pages to Confluence format and maintain synchronized documentation across platforms.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Authentication](#authentication)
  - [Configuration Parameters](#configuration-parameters)
  - [Environment Variables](#environment-variables)
- [Markdown Support](#markdown-support)
- [Usage Examples](#usage-examples)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Automated Publishing** - Seamlessly publish MkDocs documentation to Confluence during builds
- **Hierarchy Preservation** - Maintains your MkDocs navigation structure in Confluence
- **Smart Updates** - Creates new pages or updates existing ones based on title matching
- **Image Management** - Automatically uploads and updates images as attachments
- **Multiple Authentication Methods** - Supports Basic Auth, API tokens, and OAuth Bearer tokens
- **Environment Variable Support** - Secure credential management for CI/CD pipelines
- **Dry Run Mode** - Preview changes without modifying Confluence
- **Conditional Publishing** - Enable/disable based on environment variables
- **Enhanced Markdown** - Extended syntax support including strikethrough, admonitions, task lists, and more
- **Comprehensive Logging** - Verbose and debug modes for troubleshooting

## Installation

Install via pip:

```bash
pip install mkdocs-to-confluence
```

Or add to your `requirements.txt`:

```
mkdocs>=1.1
mkdocs-to-confluence
```

## Quick Start

1. **Add the plugin to your `mkdocs.yml`:**

```yaml
plugins:
  - search
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: "Documentation Home"
      username: your-email@example.com
      api_token: your-api-token-here
```

2. **Build your documentation:**

```bash
mkdocs build
```

The plugin will automatically publish your pages to Confluence during the build process.

## Configuration

### Authentication

The plugin supports three authentication methods:

#### 1. HTTP Basic Authentication with API Token (Recommended)

**For Confluence Cloud:**

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      username: your-email@example.com
      api_token: your-api-token-here
```

**Generate an API token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token

#### 2. HTTP Basic Authentication with Password

**For Confluence Server:**

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://confluence.company.com/rest/api/content
      space: DOCS
      username: your-username
      password: your-password
```

**Note:** This method is less secure. API tokens are recommended.

#### 3. OAuth Bearer Token Authentication

**For OAuth 2.0:**

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      username: your-email@example.com
      api_token: your-oauth-bearer-token
      auth_type: bearer
```

### Configuration Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `host_url` | Yes | string | Confluence REST API URL (e.g., `https://domain.atlassian.net/wiki/rest/api/content`) |
| `space` | Yes | string | Confluence space key (found in URL: `.../display/SPACEKEY/...`) |
| `parent_page_name` | No | string | Title of parent page under which documentation will be nested |
| `username` | Yes* | string | Confluence username (usually email for Cloud) |
| `password` | No | string | Confluence password (Confluence Server only) |
| `api_token` | Yes* | string | API token (Cloud) or OAuth token (with `auth_type: bearer`) |
| `auth_type` | No | string | Authentication type: `basic` (default) or `bearer` |
| `enabled_if_env` | No | string | Only publish if this environment variable is set to `"1"` |
| `dryrun` | No | boolean | Preview mode - no actual changes to Confluence (default: `false`) |
| `verbose` | No | boolean | Enable verbose logging (default: `false`) |
| `debug` | No | boolean | Enable debug logging (default: `false`) |

*Either `username`/`api_token` or environment variables must be provided.

### Environment Variables

For better security, especially in CI/CD environments, use environment variables:

| Environment Variable | Description |
|---------------------|-------------|
| `JIRA_USERNAME` | Confluence username (fallback if `username` not set) |
| `JIRA_PASSWORD` | Confluence password (fallback if `password` not set) |
| `CONFLUENCE_API_TOKEN` | API token (fallback if `api_token` not set) |

**Example with environment variables:**

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      # Credentials will be read from environment variables
```

Then set:

```bash
export JIRA_USERNAME="your-email@example.com"
export CONFLUENCE_API_TOKEN="your-token"
```

## Markdown Support

### Standard Markdown

All standard Markdown features are supported:
- Headings, paragraphs, lists
- Bold, italic, code
- Links and images
- Tables
- Code blocks with syntax highlighting

### Extended Markdown Features

This plugin uses an enhanced fork of md2cf that supports:

| Feature | Syntax | Confluence Output |
|---------|--------|-------------------|
| **Strikethrough** | `~~deleted text~~` | ~~deleted~~ |
| **Highlight** | `==marked text==` | ==highlighted== |
| **Insert** | `++inserted text++` | ++inserted++ |
| **Task Lists** | `- [ ] Todo` / `- [x] Done` | Checkboxes |
| **Admonitions** | Note/Warning/Tip blocks | Info/Warning panels |
| **Spoilers** | Expandable sections | Expand macro |
| **Block Images** | Standard image syntax | Full-width images |

### Why a Fork?

The plugin uses a vendored fork of [md2cf](https://github.com/andrust/md2cf/tree/mistune_uplift) that provides:
- Support for mistune 3.x (modern Markdown parser)
- Additional Confluence markup features
- Active maintenance and bug fixes

The fork is vendored (included in the package) to ensure reliability and avoid dependency conflicts.

## Usage Examples

### Minimal Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
```

### Production Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: "Engineering Documentation"
      enabled_if_env: PUBLISH_TO_CONFLUENCE
      verbose: true
```

### Development Configuration (Dry Run)

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DEV
      dryrun: true  # No actual changes
      debug: true   # Detailed logging
```



## Troubleshooting

### Common Issues

**1. "Authentication failed"**
- Verify username and API token are correct
- For Cloud: Use email as username
- For Server: Use username (not email)
- Check API token hasn't expired

**2. "Space not found"**
- Verify space key is correct (case-sensitive)
- Ensure your account has access to the space

**3. "Parent page not found"**
- Create the parent page in Confluence first
- Verify exact title match (case-sensitive)
- Check you have edit permissions on the parent page

**4. "Images not uploading"**
- Check image paths are correct in Markdown
- Verify image files exist in your source
- Ensure images are in supported formats (PNG, JPG, GIF, SVG)

**5. "Permission denied"**
- Verify your Confluence account has edit permissions
- Check space permissions
- For API tokens: Ensure token has write access

### Debug Mode

Enable debug logging to see detailed information:

```yaml
plugins:
  - mkdocs-to-confluence:
      debug: true
      verbose: true
```

### Dry Run Testing

Test without making changes:

```yaml
plugins:
  - mkdocs-to-confluence:
      dryrun: true
```

This shows what would be published without actually modifying Confluence.

## Requirements

- **Python**: >=3.8
- **MkDocs**: >=1.1
- **Dependencies**: jinja2, requests, mistune>=3.1.2, mime>=0.1.0

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make py-test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/jmanteau/mkdocs-to-confluence.git
cd mkdocs-to-confluence

# Set up development environment
make py-setup

# Run tests
make py-test

# Run linting
make py-ruff

# Run type checking
make py-mypy
```

See the [PUBLISHING.md](PUBLISHING.md) file for release procedures.

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

- **Issues**: [GitHub Issues](https://github.com/jmanteau/mkdocs-to-confluence/issues)

