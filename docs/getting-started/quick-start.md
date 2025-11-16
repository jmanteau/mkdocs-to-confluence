# Quick Start

Get up and running with mkdocs-to-confluence in minutes!

## Step 1: Install the Plugin

```bash
pip install mkdocs-to-confluence
```

## Step 2: Get Confluence Credentials

### API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a name and copy the token

### Space Key

Find your Confluence space key:
1. Go to your Confluence space
2. Click "Space Settings"
3. The space key is shown in the URL: `https://your-domain.atlassian.net/wiki/spaces/SPACEKEY/`

## Step 3: Configure MkDocs

Add to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: YOUR_SPACE
      parent_page_name: Documentation
      username: your-email@example.com
      api_token: your-api-token
```

!!! tip "Environment Variables"
    You can use environment variables instead of hardcoding credentials:

    ```yaml
    plugins:
      - mkdocs-to-confluence:
          host_url: https://your-domain.atlassian.net/wiki/rest/api/content
          space: YOUR_SPACE
          parent_page_name: Documentation
    ```

    Then set: `JIRA_USERNAME` and `CONFLUENCE_API_TOKEN`

## Step 4: Build Your Documentation

```bash
mkdocs build
```

Your documentation will be automatically synced to Confluence!

## Step 5: Test with Dry Run

Before syncing to production, test with dry run mode:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://your-domain.atlassian.net/wiki/rest/api/content
      space: YOUR_SPACE
      dryrun: true
      export_dir: confluence-export
```

This exports to a local directory for inspection.

## Next Steps

- [Configuration Guide](configuration.md) - Learn about all configuration options
- [Basic Usage](../user-guide/basic-usage.md) - Understand how the plugin works
- [Managing Orphaned Pages](../user-guide/managing-orphaned-pages.md) - Keep your Confluence space synchronized
- [Advanced Features](../user-guide/advanced-features.md) - Explore advanced capabilities
