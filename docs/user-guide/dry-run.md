# Dry Run and Export Modes

Validate and test your Confluence documentation before publishing.

## Overview

The plugin offers two non-production modes:

### Dry Run Mode (`dryrun: true`)

Validates against Confluence **without making changes**:

- **Connects to Confluence** in read-only mode
- Validates all pages against existing content
- Performs content comparisons to detect changes
- Detects orphaned pages
- Shows what would be modified ("*WOULD UPDATE*", "*WOULD CREATE*")
- **Does NOT** create, update, or delete anything
- Requires valid Confluence credentials

**Use for:** CI/CD validation, preview changes, check orphaned pages

### Export-Only Mode (`export_only: true`)

Exports to filesystem **without connecting to Confluence**:

- **No Confluence connection** required
- Exports pages to local filesystem in Confluence format
- No validation or comparisons
- Faster than dryrun (no API calls)
- Works offline

**Use for:** Generate HTML for manual upload, offline development, archive documentation

!!! info "Changed in 0.7.0"
    Previously, `dryrun` exported to filesystem. Now it connects to Confluence for validation.
    Use `export_only: true` for the old behavior.

## Configuration

### Dry Run Mode (Validation)

Enable read-only validation against Confluence:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: Documentation
      username: !ENV JIRA_USERNAME
      api_token: !ENV CONFLUENCE_API_TOKEN
      dryrun: true  # Connects to Confluence in read-only mode
```

### Export-Only Mode (Filesystem)

Enable filesystem export without Confluence connection:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content  # Not used in export_only
      space: DOCS
      parent_page_name: Documentation
      export_only: true  # No Confluence connection
      export_dir: confluence-export
```

## Dry Run Mode Output

When running with `dryrun: true`, the plugin connects to Confluence and shows what would be done:

```bash
mkdocs build
```

Output:

```
INFO - Mkdocs With Confluence v0.7.0
INFO - Mkdocs With Confluence - DRYRUN MODE turned ON (read-only, no modifications)
INFO - Number of files in directory tree: 15

# Existing pages with no changes
INFO - Mkdocs With Confluence: Home - *NO CHANGE*

# Existing pages that would be updated
INFO - Mkdocs With Confluence: Getting Started - *WOULD UPDATE* (dryrun)

# New pages that would be created
INFO - Mkdocs With Confluence: New Feature - *WOULD CREATE* (dryrun)

# Orphaned pages detected
WARNING - Mkdocs With Confluence: Found 2 orphaned page(s) in Confluence:
WARNING -   - Old Documentation
WARNING -   - Deprecated Guide
INFO - Run with 'cleanup_orphaned_pages: true' to delete them (dryrun mode)
```

Key behaviors:
- Fetches existing pages from Confluence
- Compares content to detect changes
- Shows "*WOULD UPDATE*" for modified pages
- Shows "*WOULD CREATE*" for new pages
- Detects orphaned pages
- **Does not modify anything** on Confluence

## Export Structure (Export-Only Mode)

When using `export_only: true`, pages are saved to filesystem:

### Directory Layout

```
confluence-export/
├── metadata.json
├── Home/
│   ├── page.html
│   ├── metadata.json
│   └── attachments/
│       └── logo.png
├── Getting Started/
│   ├── page.html
│   ├── metadata.json
│   ├── Installation/
│   │   ├── page.html
│   │   └── metadata.json
│   └── Quick Start/
│       ├── page.html
│       └── metadata.json
└── API Reference/
    ├── page.html
    └── metadata.json
```

### Root Metadata

`confluence-export/metadata.json`:

```json
{
  "space": "DOCS",
  "export_date": "2025-11-13T10:30:00",
  "total_pages": 5,
  "root_pages": [
    "Home",
    "Getting Started",
    "API Reference"
  ]
}
```

### Page Metadata

Each `metadata.json` contains:

```json
{
  "title": "Installation",
  "parent": "Getting Started",
  "space": "DOCS",
  "attachments": [],
  "children": []
}
```

### Page Content

`page.html` contains Confluence-formatted HTML:

```html
<h2>Installation</h2>
<p>Install via pip:</p>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[pip install our-package]]></ac:plain-text-body>
</ac:structured-macro>
```

## Build and Export (Export-Only)

With `export_only: true`:

```bash
mkdocs build
```

Output:

```
INFO - Mkdocs With Confluence v0.7.0
INFO - Mkdocs With Confluence - EXPORT ONLY MODE turned ON (no Confluence connection)
INFO - Mkdocs With Confluence: Exporting to confluence-export
INFO - Number of files in directory tree: 15

INFO - Mkdocs With Confluence: Home - *QUEUED FOR EXPORT*
INFO - Mkdocs With Confluence: Getting Started - *QUEUED FOR EXPORT*
INFO - Mkdocs With Confluence: Installation - *QUEUED FOR EXPORT*

INFO - Mkdocs With Confluence: Exporting all pages to filesystem...
INFO - Mkdocs With Confluence: Export complete! Files saved to /path/to/confluence-export
```

## Inspecting Exports

### View Structure

```bash
tree confluence-export/
```

### View Page Content

```bash
cat "confluence-export/Getting Started/page.html"
```

### Check Metadata

```bash
cat confluence-export/metadata.json | jq
```

### View Attachments

```bash
ls "confluence-export/Home/attachments/"
```

## Validation

### Verify Hierarchy

Check parent relationships:

```bash
# View all page metadata
find confluence-export -name "metadata.json" -exec cat {} \;
```

### Check Content

Look for conversion issues:

```bash
# Search for unconverted Markdown
grep -r "```" confluence-export/
```

### Validate Links

Ensure internal links are properly converted:

```bash
grep -r "href=" confluence-export/ | grep -v "http"
```

## Testing Workflow

### 1. Dry Run Export

```yaml
dryrun: true
export_dir: test-export
```

```bash
mkdocs build
```

### 2. Review Output

```bash
# View structure
tree test-export/

# Check a specific page
cat test-export/Getting\ Started/page.html

# Verify metadata
cat test-export/metadata.json | jq '.total_pages'
```

### 3. Fix Issues

Update your Markdown or configuration, then rebuild.

### 4. Deploy to Confluence

```yaml
dryrun: false
```

```bash
mkdocs build
```

## Cleanup

Remove export directory:

```bash
make clean
```

Or manually:

```bash
rm -rf confluence-export/
```

## Common Use Cases

### Validate Before Publishing (Dryrun)

Use dryrun to validate against Confluence without making changes:

```bash
# Validate in dryrun mode
mkdocs build  # with dryrun: true in config

# Review what would be changed
# Look for "*WOULD UPDATE*" and "*WOULD CREATE*" messages

# Deploy to production
# Change dryrun: false, then mkdocs build
```

### CI/CD Validation Workflow

```yaml
# .github/workflows/docs.yml
- name: Validate documentation (dryrun)
  env:
    JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
    CONFLUENCE_API_TOKEN: ${{ secrets.CONFLUENCE_API_TOKEN }}
    CONFLUENCE_DRYRUN: "true"
  run: |
    mkdocs build --strict  # Validates against Confluence
    # Build fails if validation finds issues

- name: Publish to Confluence
  env:
    JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
    CONFLUENCE_API_TOKEN: ${{ secrets.CONFLUENCE_API_TOKEN }}
    CONFLUENCE_DRYRUN: "false"
  run: |
    mkdocs build  # Actually publishes
```

### Offline Development (Export-Only)

Use export_only for development without Confluence access:

```bash
# Export to filesystem (no Confluence needed)
mkdocs build  # with export_only: true in config

# Review HTML files
ls -R confluence-export/
cat "confluence-export/Getting Started/page.html"

# Check page count
PAGES=$(cat confluence-export/metadata.json | jq '.total_pages')
echo "Exported $PAGES pages"
```

### Environment-Based Configuration

Control modes via environment variables:

```yaml
# mkdocs.yml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      username: !ENV JIRA_USERNAME
      api_token: !ENV CONFLUENCE_API_TOKEN
      dryrun: !ENV [CONFLUENCE_DRYRUN, false]
      export_only: !ENV [CONFLUENCE_EXPORT_ONLY, false]
      export_dir: confluence-export
```

```bash
# Validate against Confluence (dryrun)
CONFLUENCE_DRYRUN=true mkdocs build

# Export to filesystem (export_only)
CONFLUENCE_EXPORT_ONLY=true mkdocs build

# Publish to Confluence (normal)
mkdocs build
```

## Troubleshooting

### Dryrun Mode Issues

#### Connection Errors in Dryrun

If dryrun fails to connect to Confluence:

```
ERROR - Cannot connect to Confluence: Connection refused
```

Check:
- Credentials are set (`JIRA_USERNAME`, `CONFLUENCE_API_TOKEN`)
- `host_url` is correct
- Network access to Confluence

**Solution:** Use `export_only: true` if you don't need validation

#### Authentication Failures

```
ERROR - 403 Client Error: Forbidden
```

Check:
- API token has correct permissions
- Username matches the token owner
- Space is accessible by the user

### Export-Only Mode Issues

#### Export Directory Not Created

Check plugin configuration:

```yaml
plugins:
  - mkdocs-to-confluence:  # Correct
      export_only: true

  # NOT:
  - mkdocs-to-confluence  # Wrong - no configuration
```

#### Missing Pages

Ensure pages are in navigation:

```yaml
nav:
  - Home: index.md
  - Guide: guide.md  # Must be in nav to export
```

### General Issues

#### Incorrect Hierarchy

In export_only mode, check `parent` field in metadata files. Should match your navigation structure.

#### Malformed HTML

Enable debug mode to see conversion details:

```yaml
export_only: true  # or dryrun: true
debug: true
```

Check `/tmp/mkdocs-to-confluence-debug/` for intermediate files.

## Next Steps

- [Basic Usage](basic-usage.md) - Understand normal operation
- [Advanced Features](advanced-features.md) - Explore capabilities
- [Configuration Reference](../getting-started/configuration.md) - All options
