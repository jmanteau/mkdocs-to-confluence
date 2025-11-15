# Configuration Reference

Complete reference for all mkdocs-to-confluence configuration options.

## Basic Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: YOUR_SPACE
      parent_page_name: Documentation
      username: your-email@example.com
      api_token: your-api-token
```

## Configuration Options

### Required Settings

#### `host_url`

The Confluence REST API endpoint URL.

**Format:** `https://your-domain.atlassian.net/wiki/rest/api/content`

```yaml
host_url: https://company.atlassian.net/wiki/rest/api/content
```

#### `space`

The Confluence space key where pages will be created.

```yaml
space: DEV
```

### Authentication

#### `username`

Your Confluence username (email address).

**Default:** Environment variable `JIRA_USERNAME`

```yaml
username: user@example.com
```

#### `api_token`

Your Confluence API token. **Never commit this to version control!**

**Default:** Environment variable `CONFLUENCE_API_TOKEN`

```yaml
api_token: your-secret-token
```

!!! warning "Security"
    Use environment variables instead of hardcoding credentials:
    ```bash
    export JIRA_USERNAME=user@example.com
    export CONFLUENCE_API_TOKEN=your-token
    ```

#### `password`

Legacy password authentication (not recommended). Use `api_token` instead.

**Default:** Environment variable `JIRA_PASSWORD`

#### `auth_type`

Authentication method: `basic` (default) or `bearer` for OAuth tokens.

```yaml
auth_type: basic  # or 'bearer'
```

### Page Hierarchy

#### `parent_page_name`

The parent page under which all documentation pages will be created.

**Default:** Uses `space` value if not specified

```yaml
parent_page_name: API Documentation
```

### Features

#### `strip_h1`

Automatically remove H1 headings from page content (since Confluence displays the page title).

**Default:** `false`

```yaml
strip_h1: true
```

Only strips if:
- H1 is the first content element
- There's exactly one H1 in the document

#### `dryrun`

Enable dry-run mode to export pages to filesystem instead of uploading to Confluence.

**Default:** `false`

```yaml
dryrun: true
export_dir: confluence-export
```

#### `export_dir`

Directory for dry-run exports.

**Default:** `confluence-export`

```yaml
export_dir: my-export-folder
```

### Conditional Execution

#### `enabled_if_env`

Only enable the plugin if a specific environment variable is set to `1`.

```yaml
enabled_if_env: PUBLISH_TO_CONFLUENCE
```

```bash
# Enable publishing
export PUBLISH_TO_CONFLUENCE=1
mkdocs build

# Skip publishing
unset PUBLISH_TO_CONFLUENCE
mkdocs build
```

### Logging

#### `verbose`

Enable verbose logging output.

**Default:** `false`

```yaml
verbose: true
```

#### `debug`

Enable debug mode with detailed logging and temporary file creation.

**Default:** `false`

```yaml
debug: true
```

When enabled:
- Writes comparison files to `/tmp/confluence-debug/`
- Logs content changes and API responses
- Saves intermediate HTML files

## Complete Example

```yaml
site_name: My Documentation
plugins:
  - mkdocs-to-confluence:
      # Connection
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS

      # Authentication (use environment variables in production!)
      username: user@example.com
      api_token: ${CONFLUENCE_API_TOKEN}
      auth_type: basic

      # Hierarchy
      parent_page_name: Product Documentation

      # Features
      strip_h1: true

      # Testing
      dryrun: false
      export_dir: confluence-export

      # Logging
      verbose: false
      debug: false

      # Conditional
      enabled_if_env: PUBLISH_DOCS
```

## Environment-Based Configuration

Recommended production setup:

### mkdocs.yml

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: Documentation
      strip_h1: true
      enabled_if_env: PUBLISH_TO_CONFLUENCE
```

### Environment Variables

```bash
# .env file (never commit!)
export JIRA_USERNAME=user@example.com
export CONFLUENCE_API_TOKEN=your-secret-token
export PUBLISH_TO_CONFLUENCE=1
```

### CI/CD Configuration

```yaml
# .github/workflows/docs.yml
- name: Build and Deploy Docs
  env:
    JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
    CONFLUENCE_API_TOKEN: ${{ secrets.CONFLUENCE_API_TOKEN }}
    PUBLISH_TO_CONFLUENCE: "1"
  run: mkdocs build
```

## Next Steps

- [Basic Usage](../user-guide/basic-usage.md) - Learn how to use the plugin
- [Advanced Features](../user-guide/advanced-features.md) - Explore advanced capabilities
- [Dry Run Mode](../user-guide/dry-run.md) - Test before publishing
