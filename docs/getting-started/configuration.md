---
title: Configuration Tutorial
---

# Configuring Your Plugin

Learn how to configure mkdocs-to-confluence to publish your documentation to Confluence.

## Step 1: Add Plugin to mkdocs.yml

Open your `mkdocs.yml` and add the plugin:

```yaml
plugins:
  - search  # Keep your existing plugins
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: YOUR_SPACE
      parent_page_name: Documentation
```

## Step 2: Configure Authentication

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

## Step 3: Find Your Space Key

Your Confluence space key appears in the URL:

```
https://your-domain.atlassian.net/wiki/spaces/SPACEKEY/overview
                                                  ^^^^^^^^
```

Or find it in Confluence:
1. Navigate to your space
2. Click "Space Settings" (gear icon)
3. Look for "Space Key" in the overview

## Step 4: Test with Dry Run

Before publishing to Confluence, test locally:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      dryrun: true
      export_dir: confluence-export
```

Build your docs:

```bash
mkdocs build
```

Check the `confluence-export/` directory to preview the converted pages.

## Step 5: Publish to Confluence

Remove or set `dryrun: false` to publish:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: Documentation
      dryrun: false  # Or remove this line
```

Build again:

```bash
mkdocs build
```

Your pages are now published to Confluence! 🎉

## Common Configuration Options

### Strip H1 Headings

Remove redundant H1 headings (Confluence shows page title):

```yaml
plugins:
  - mkdocs-to-confluence:
      strip_h1: true
```

### Conditional Publishing

Only publish when an environment variable is set:

```yaml
plugins:
  - mkdocs-to-confluence:
      enabled_if_env: PUBLISH_TO_CONFLUENCE
```

```bash
export PUBLISH_TO_CONFLUENCE=1
mkdocs build  # Will publish

unset PUBLISH_TO_CONFLUENCE
mkdocs build  # Will skip publishing
```

### Enable Verbose Logging

See detailed output during publishing:

```yaml
plugins:
  - mkdocs-to-confluence:
      verbose: true
```

## Complete Example

Here's a production-ready configuration:

```yaml
site_name: My Documentation

plugins:
  - search
  - mkdocs-to-confluence:
      # Connection
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: Product Documentation

      # Features
      strip_h1: true

      # Control
      enabled_if_env: PUBLISH_TO_CONFLUENCE

      # Credentials (set via environment variables)
      # JIRA_USERNAME and CONFLUENCE_API_TOKEN
```

Set environment variables:

```bash
# .env file (never commit!)
export JIRA_USERNAME=user@example.com
export CONFLUENCE_API_TOKEN=your-secret-token
export PUBLISH_TO_CONFLUENCE=1
```

## Next Steps

- **[Basic Usage](../user-guide/basic-usage.md)** - Learn the publishing workflow
- **[Configuration Reference](../reference/configuration.md)** - Complete configuration options
- **[Dry Run Mode](../user-guide/dry-run.md)** - Test before publishing
- **[Troubleshooting](../troubleshooting.md)** - Common issues and solutions
