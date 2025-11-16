---
title: Key Concepts
---

# Understanding mkdocs-to-confluence

Core concepts for working with the plugin and understanding how documentation maps to Confluence.

## Pages

### MkDocs Pages

In MkDocs, pages are Markdown files organized in a directory structure:

```
docs/
├── index.md
├── getting-started/
│   ├── installation.md
│   └── quick-start.md
└── user-guide/
    └── usage.md
```

### Confluence Pages

In Confluence, pages exist in a flat namespace within a space, but can have parent-child relationships:

```
SPACE: DOCS
├── Documentation (parent)
│   ├── Installation
│   ├── Quick Start
│   └── Usage
```

### Mapping

The plugin maps MkDocs directory structure to Confluence hierarchy:

- **File path** determines hierarchy (subdirectories become child pages)
- **File name** becomes page title (or title from frontmatter)
- **Navigation order** in `mkdocs.yml` determines Confluence page order

## Hierarchy

### Parent Pages

The `parent_page_name` configuration determines where your documentation tree begins:

```yaml
plugins:
  - mkdocs-to-confluence:
      parent_page_name: API Documentation
```

All MkDocs pages become children (or descendants) of this parent page.

### Nested Structure

The plugin supports unlimited nesting depth:

```
docs/
└── api/
    └── v2/
        └── endpoints/
            └── users.md
```

Becomes:

```
Parent Page
└── API
    └── V2
        └── Endpoints
            └── Users
```

### Root vs Parent

**Without `parent_page_name`:**
Pages are created as direct children of the space root.

**With `parent_page_name`:**
Pages are created under the specified parent page.

## Content Synchronization

### Title Matching

Confluence pages are identified by **title** within a space. The plugin:

1. Searches for existing page with matching title
2. Creates new page if not found
3. Updates existing page if found

**Important:** Renaming a page in MkDocs creates a new page in Confluence (old page remains).

### Content Changes

The plugin detects changes by comparing normalized content:

- **Content changed** → Update page (new version in Confluence)
- **Content identical** → Skip update (no new version)

This prevents unnecessary version bumps in Confluence.

### Update Behavior

```
First build:    Creates all pages
Second build:   Updates only changed pages
Third build:    Skips pages with no changes
```

## Attachments

### Images

Images referenced in Markdown become Confluence attachments:

```markdown
![Architecture](images/arch.png)
```

The plugin:
1. Uploads `images/arch.png` as attachment to the page
2. Updates page content with attachment reference
3. Tracks attachment via SHA1 hash
4. Re-uploads only if image content changes

### Attachment Updates

Attachments are versioned in Confluence:

- **First upload** → Creates attachment (version 1)
- **Content changed** → Updates attachment (version 2)
- **Content identical** → Skips update (stays version 1)

### Supported Formats

- PNG, JPG, JPEG, GIF - Displayed inline
- SVG - Support depends on Confluence version
- PDF, other files - Downloadable attachments

## Spaces

### Confluence Spaces

A space is a container for related pages in Confluence. Each space has:

- **Space Key** - Unique identifier (e.g., "DOCS", "DEV")
- **Space Name** - Human-readable name
- **Permissions** - Who can view/edit

### Plugin Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      space: DOCS  # Space key (case-sensitive!)
```

All pages are created within this space.

### Multi-Space Publishing

To publish to multiple spaces, use multiple plugin configurations (requires MkDocs plugin chaining).

## Authentication

### API Tokens

Confluence Cloud uses API tokens for authentication:

```bash
export JIRA_USERNAME=user@example.com
export CONFLUENCE_API_TOKEN=token123
```

- **Username** is your email address
- **Token** is generated from Atlassian account settings
- Never commit tokens to version control

### Token Permissions

API tokens inherit the user's permissions. Ensure your account has:

- View/edit access to target space
- Permission to create pages
- Permission to upload attachments

### Server vs Cloud

- **Confluence Cloud** - Use API tokens (recommended)
- **Confluence Server** - Use API tokens or password (legacy)

## Build Integration

### MkDocs Build

The plugin runs during `mkdocs build`:

```bash
mkdocs build   # Builds HTML and syncs to Confluence
```

### Conditional Publishing

Control when publishing occurs:

```yaml
plugins:
  - mkdocs-to-confluence:
      enabled_if_env: PUBLISH_DOCS
```

```bash
# Publish
PUBLISH_DOCS=1 mkdocs build

# Skip publishing
mkdocs build
```

Useful for:
- CI/CD pipelines (publish only on main branch)
- Local development (disable publishing)
- Different environments (staging vs production)

## Storage Format

### Confluence Storage Format

Confluence uses XHTML-based storage format with custom macros:

```xml
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[code here]]></ac:plain-text-body>
</ac:structured-macro>
```

The plugin handles conversion automatically.

### Why Storage Format?

- **Editor-agnostic** - Works with all Confluence editors
- **Structured** - Preserves semantic meaning
- **Macros** - Supports rich Confluence features

## Page Versions

### Confluence Versioning

Every page update creates a new version in Confluence:

```
Version 1: Initial creation
Version 2: Content updated
Version 3: Content updated again
```

### Version History

Users can:
- View previous versions
- Compare versions
- Restore old versions

### Minimizing Versions

The plugin's change detection prevents unnecessary versions:

- Only updates when content actually changes
- Normalizes whitespace/formatting differences
- Compares semantic content, not raw HTML

This keeps version history clean and meaningful.

## Dry Run Mode

### Testing Without Publishing

Dry run exports pages to filesystem instead of Confluence:

```yaml
plugins:
  - mkdocs-to-confluence:
      dryrun: true
      export_dir: confluence-export
```

### Use Cases

- **Preview** - See converted content before publishing
- **Debugging** - Inspect HTML conversion
- **Testing** - Verify configuration
- **CI/CD** - Test docs build without credentials

### Output Structure

```
confluence-export/
├── metadata.json          # Page metadata
├── Page_One.html         # Converted pages
├── Page_Two.html
└── attachments/          # Images
    └── diagram.png
```

## Markdown Extensions

### Supported Syntax

The plugin supports extended Markdown:

- **Tables** - Converted to Confluence tables
- **Code blocks** - Wrapped in code macros with syntax highlighting
- **Admonitions** - Converted to info/warning panels
- **Task lists** - Converted to checkboxes
- **Strikethrough** - Preserved
- **Footnotes** - Converted to references

### Confluence Limitations

Some Markdown features have limitations:

- **Nested lists** - Complex nesting may not render perfectly
- **HTML** - Raw HTML is sanitized by Confluence
- **Custom CSS** - Not supported
- **JavaScript** - Not supported

See [Markdown Showcase](../markdown-showcase.md) for examples.

## Next Steps

- [How It Works](architecture.md) - Plugin architecture deep dive
- [Configuration Reference](../reference/configuration.md) - All options
- [Basic Usage](../user-guide/basic-usage.md) - Publishing workflow
