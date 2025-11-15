# Basic Usage

Learn how to use mkdocs-to-confluence for your documentation workflow.

## How It Works

The plugin integrates into the MkDocs build process:

1. **Build Phase** - MkDocs renders your Markdown to HTML
2. **Conversion** - Plugin converts HTML to Confluence storage format
3. **Sync** - Plugin uploads pages to Confluence via REST API
4. **Update Detection** - Only updates pages when content changes

## Basic Workflow

### 1. Write Your Documentation

Create Markdown files in your `docs/` directory:

```markdown
# Getting Started

Welcome to our documentation!

## Installation

Install via pip:

\`\`\`bash
pip install our-package
\`\`\`
```

### 2. Configure MkDocs

Add the plugin to `mkdocs.yml`:

```yaml
site_name: My Docs
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: Documentation
```

### 3. Build and Sync

```bash
mkdocs build
```

Your pages are now on Confluence!

## Page Hierarchy

The plugin maintains your documentation structure in Confluence.

### MkDocs Navigation

```yaml
nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
  - API Reference:
      - REST API: api/rest.md
      - WebSocket: api/websocket.md
```

### Resulting Confluence Structure

```
Documentation (parent page)
├── Home
├── Getting Started
│   ├── Installation
│   └── Quick Start
└── API Reference
    ├── REST API
    └── WebSocket
```

## Update Behavior

### Creating New Pages

When you add a new page to your docs:

```yaml
nav:
  - Home: index.md
  - New Guide: new-guide.md  # ← New page
```

The plugin:
1. Creates the page in Confluence
2. Sets the correct parent relationship
3. Logs: `Mkdocs With Confluence: New Guide *NEW PAGE*`

### Updating Existing Pages

When you modify content:

```markdown
# Getting Started

Updated content here...
```

The plugin:
1. Fetches current Confluence content
2. Compares with new content
3. Only updates if changed
4. Logs: `Mkdocs With Confluence: Getting Started *UPDATE*`

### No Changes

If content is unchanged:

```
Mkdocs With Confluence: Getting Started *NO CHANGE*
```

No API call is made - saves time and avoids unnecessary version bumps!

## Attachments

### Images

Images are automatically uploaded as attachments:

```markdown
![Architecture Diagram](images/architecture.png)
```

The plugin:
1. Detects image references
2. Uploads images as attachments
3. Updates image references in Confluence
4. Logs: `* Attachment: architecture.png - *NEW*`

### Supported Formats

- PNG, JPG, GIF images
- SVG diagrams
- PDF files
- Any file referenced in Markdown

## Output Logging

### Normal Mode

Minimal progress indicator:

```
INFO - Mkdocs With Confluence: Page export progress: [###-------] (3 / 10)
INFO - Mkdocs With Confluence: Getting Started *UPDATE*
INFO - Mkdocs With Confluence: API Reference *NO CHANGE*
```

### Verbose Mode

```yaml
verbose: true
```

Shows detailed operation logs.

### Debug Mode

```yaml
debug: true
```

Enables:
- Content comparison details
- Temporary debug files in `/tmp/confluence-debug/`
- API request/response logging
- Diff commands for manual inspection

## Common Workflows

### Local Development

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DEV
      dryrun: true  # Test locally
      export_dir: confluence-export
```

View exported files before publishing.

### CI/CD Pipeline

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: PROD
      enabled_if_env: PUBLISH_TO_CONFLUENCE
```

Only publish on specific branches or conditions.

### Preview Changes

```bash
# Export to local directory
mkdocs build

# Inspect exported files
ls confluence-export/

# Deploy to Confluence
PUBLISH_TO_CONFLUENCE=1 mkdocs build
```

## Next Steps

- [Advanced Features](advanced-features.md) - Explore advanced capabilities
- [Dry Run Mode](dry-run.md) - Test exports locally
- [Configuration Reference](../getting-started/configuration.md) - All options
