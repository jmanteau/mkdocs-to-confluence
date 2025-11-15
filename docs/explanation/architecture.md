---
title: How It Works
---

# Plugin Architecture

Understanding how mkdocs-to-confluence converts and publishes your documentation to Confluence.

## Overview

The plugin integrates with the MkDocs build pipeline, intercepting the build process to convert Markdown to Confluence storage format and upload pages via the Confluence REST API.

## Build Pipeline Integration

### MkDocs Hooks

The plugin uses MkDocs event hooks to integrate into the build process:

```
mkdocs build
    ↓
on_config()      → Validate plugin configuration
    ↓
on_files()       → Discover documentation files
    ↓
on_page_markdown() → Process each page's Markdown
    ↓
on_page_content() → Convert to Confluence format
    ↓
on_post_build()  → Upload to Confluence
```

### Key Phases

**1. Configuration Phase** (`on_config`)
- Validates required settings (host_url, space, credentials)
- Establishes authentication session
- Resolves parent page hierarchy

**2. Discovery Phase** (`on_files`)
- Maps MkDocs navigation to Confluence page hierarchy
- Resolves parent-child relationships
- Builds dependency tree for correct upload order

**3. Conversion Phase** (`on_page_content`)
- Converts Markdown to Confluence storage format (XHTML)
- Extracts image references
- Transforms links for Confluence

**4. Upload Phase** (`on_post_build`)
- Checks if pages already exist (by title)
- Compares content to detect changes
- Creates or updates pages
- Uploads attachments (images)
- Maintains page hierarchy

## Content Conversion

### Markdown to Confluence Storage Format

Confluence uses a storage format based on XHTML with custom macros. The plugin:

1. **Parses Markdown** using mistune 3.x parser
2. **Converts to XHTML** with Confluence-specific transformations
3. **Wraps code blocks** in Confluence code macros
4. **Converts admonitions** to Confluence info/warning panels
5. **Transforms tables** to Confluence table format
6. **Handles images** as attachment references

Example transformation:

```markdown
# My Page

Some **bold** text.

\```python
print("hello")
\```
```

Becomes:

```xml
<h1>My Page</h1>
<p>Some <strong>bold</strong> text.</p>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[print("hello")]]></ac:plain-text-body>
</ac:structured-macro>
```

### Image Handling

Images are handled as Confluence attachments:

1. **Extract** image references from Markdown
2. **Resolve** file paths relative to docs directory
3. **Calculate** SHA1 hash of image content
4. **Compare** hash with existing attachment (if any)
5. **Upload** only if changed or new
6. **Update** page content with attachment references

## Confluence API Integration

### REST API Operations

The plugin uses Confluence's REST API v1:

**Page Operations:**
- `GET /rest/api/content?title={title}&spaceKey={space}` - Find existing page
- `POST /rest/api/content` - Create new page
- `PUT /rest/api/content/{id}` - Update existing page

**Attachment Operations:**
- `GET /rest/api/content/{id}/child/attachment` - List attachments
- `POST /rest/api/content/{id}/child/attachment` - Upload attachment
- `PUT /rest/api/content/{id}/child/attachment/{attachmentId}/data` - Update attachment

### Authentication Methods

**Basic Auth (API Token)**
```
Authorization: Basic base64(email:api_token)
```

**Bearer Auth (OAuth)**
```
Authorization: Bearer {oauth_token}
```

### Page Hierarchy

Pages are created with parent-child relationships:

```
Space Root
└── Parent Page (parent_page_name)
    ├── Page 1
    │   ├── Page 1.1
    │   └── Page 1.2
    └── Page 2
```

The plugin:
1. Resolves parent page by name
2. Creates pages in dependency order (parents before children)
3. Waits for newly created parents before creating children
4. Supports arbitrary nesting depth

## Change Detection

### Content Normalization

To avoid unnecessary updates, content is normalized before comparison:

1. **Strip** whitespace variations
2. **Remove** Confluence metadata (version info, timestamps)
3. **Normalize** HTML formatting
4. **Compare** normalized content

Only if content differs after normalization is an update performed.

### Benefits

- Reduces Confluence version history clutter
- Avoids triggering watches/notifications unnecessarily
- Improves build performance
- Respects Confluence rate limits

## Dry Run Mode

### Local Export

Instead of uploading to Confluence, pages are exported to filesystem:

```
confluence-export/
├── metadata.json          # All pages metadata
├── Page_Title.html        # Converted HTML
└── attachments/
    └── image.png          # Copied images
```

### Use Cases

- Preview converted content
- Debug conversion issues
- Test configuration changes
- Review hierarchy structure

## Error Handling

### Retry Logic

The plugin implements retry logic for transient failures:

- Network errors → Retry with exponential backoff
- Rate limits → Wait and retry
- Parent page not ready → Poll until available

### Failure Modes

**Hard Failures** (build stops):
- Invalid credentials
- Missing required configuration
- Space not found
- Parent page not found

**Soft Failures** (logged, continue):
- Individual page upload failure
- Attachment upload failure
- Content comparison failure

## Performance Considerations

### Parallel Operations

Where possible, operations run in parallel:
- Attachment uploads for same page
- Content conversion for multiple pages

### Caching

- API responses cached during build
- Page ID lookups cached
- Parent chain resolution cached

### Rate Limiting

Respects Confluence API rate limits:
- Delays between requests
- Exponential backoff on 429 responses
- Configurable timeouts

## Security

### Credential Management

Credentials should use environment variables:

```bash
export JIRA_USERNAME=user@example.com
export CONFLUENCE_API_TOKEN=secret
```

Never hardcode credentials in `mkdocs.yml`.

### TLS/SSL

All API requests use HTTPS. Certificate validation is enforced.

### Token Scopes

API tokens should have minimal required permissions:
- Read/write access to target space
- Create/update pages
- Upload attachments

## Next Steps

- [Key Concepts](concepts.md) - Understanding pages, hierarchy, and content
- [Configuration Reference](../reference/configuration.md) - All configuration options
- [Troubleshooting](../troubleshooting.md) - Common issues
