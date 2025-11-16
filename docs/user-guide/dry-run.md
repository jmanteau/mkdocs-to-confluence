# Dry Run Mode

Test your Confluence exports locally before publishing.

## Overview

Dry run mode exports your documentation to a local filesystem instead of uploading to Confluence. This lets you:

- Preview the export structure
- Inspect converted HTML
- Verify page hierarchy
- Test configuration changes
- Review before production deploy

## Configuration

Enable dry run mode in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      parent_page_name: Documentation
      dryrun: true
      export_dir: confluence-export
```

## Export Structure

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

## Build and Export

```bash
mkdocs build
```

Output:

```
INFO - Mkdocs With Confluence: Exporting to confluence-export
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

### Preview Before Production

```bash
# Test export locally
DRYRUN=true mkdocs build

# Review
ls -R confluence-export/

# Deploy to production
DRYRUN=false PUBLISH_TO_CONFLUENCE=1 mkdocs build
```

### CI/CD Testing

```yaml
# .github/workflows/test-docs.yml
- name: Test Documentation Export
  run: |
    # Export to filesystem
    mkdocs build

    # Verify export
    test -d confluence-export
    test -f confluence-export/metadata.json

    # Check page count
    PAGES=$(cat confluence-export/metadata.json | jq '.total_pages')
    echo "Exported $PAGES pages"
```

### Development Workflow

```yaml
# mkdocs.yml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      # Use environment variable to control mode
      dryrun: !ENV [DRYRUN, false]
      export_dir: confluence-export
```

```bash
# Development: dry run
DRYRUN=true mkdocs build

# Production: real upload
DRYRUN=false mkdocs build
```

## Troubleshooting

### Export Directory Not Created

Check plugin configuration:

```yaml
plugins:
  - mkdocs-to-confluence:  # Correct
      dryrun: true

  # NOT:
  - mkdocs-to-confluence  # Wrong - no configuration
```

### Missing Pages

Ensure pages are in navigation:

```yaml
nav:
  - Home: index.md
  - Guide: guide.md  # Must be in nav to export
```

### Incorrect Hierarchy

Check `parent` field in metadata files. Should match your navigation structure.

### Malformed HTML

Enable debug mode to see conversion details:

```yaml
dryrun: true
debug: true
```

Check `/tmp/mkdocs-to-confluence-debug/` for intermediate files.

## Next Steps

- [Basic Usage](basic-usage.md) - Understand normal operation
- [Advanced Features](advanced-features.md) - Explore capabilities
- [Configuration Reference](../getting-started/configuration.md) - All options
