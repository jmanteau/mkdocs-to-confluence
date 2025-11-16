# Advanced Features

Explore advanced capabilities of mkdocs-to-confluence.

## H1 Heading Strip

Remove redundant H1 headings from your pages since Confluence displays the page title.

### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      strip_h1: true
```

### Behavior

**Before:**
```markdown
# Getting Started

Welcome to the guide...
```

**Confluence Display:**
- Page title: "Getting Started" (from navigation)
- Content: Starts with "Welcome to the guide..."

### Rules

The plugin only strips H1 if:

1. **First Content Element** - H1 is the very first content (ignoring blank lines)
2. **Single H1** - There's exactly one H1 in the entire document

This ensures accidental stripping doesn't occur.

### Supported Syntax

Both Markdown H1 styles are supported:

**ATX Style:**
```markdown
# Title
```

**Setext Style:**
```markdown
Title
=====
```

## Intelligent Content Change Detection

The plugin compares content before updating to avoid unnecessary changes.

### How It Works

1. **Fetch Current** - Gets existing Confluence content
2. **Normalize** - Removes Confluence-added metadata
3. **Compare** - Checks if actual content changed
4. **Update** - Only updates if different

### Normalization

Removes Confluence-added elements:

- `ac:schema-version` attributes
- `ac:macro-id` UUIDs
- Self-closing tag conversions
- Whitespace variations

### Benefits

- **Faster Builds** - Skips unchanged pages
- **Cleaner History** - No unnecessary version bumps
- **Reduced API Calls** - Saves rate limits

### Debug Comparison

Enable debug mode to inspect:

```yaml
debug: true
```

Creates comparison files:

```
/tmp/confluence-debug/
├── Page_Title_current.html
├── Page_Title_new.html
├── Page_Title_current_normalized.html
└── Page_Title_new_normalized.html
```

Compare with:
```bash
diff /tmp/confluence-debug/Page_Title_current_normalized.html \
     /tmp/confluence-debug/Page_Title_new_normalized.html
```

## Unlimited Hierarchy Depth

Support for arbitrarily nested page structures.

### Example Structure

```yaml
nav:
  - Home: index.md
  - Guides:
      - Getting Started:
          - Installation:
              - Linux: guides/install/linux.md
              - macOS: guides/install/macos.md
              - Windows: guides/install/windows.md
          - Configuration:
              - Basic: guides/config/basic.md
              - Advanced: guides/config/advanced.md
```

### Parent Chain Resolution

The plugin:

1. Resolves full parent chain: `["Home", "Guides", "Getting Started", "Installation"]`
2. Ensures each level exists in Confluence
3. Creates missing parent pages automatically
4. Sets correct ancestry relationships

### Automatic Page Creation

If a parent doesn't exist:

```
INFO - Trying to ADD page 'Getting Started' to parent(Guides) ID: 12345
INFO - Mkdocs With Confluence: Getting Started *NEW PAGE*
```

## Bearer Token Authentication

Support for OAuth 2.0 bearer token authentication.

### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      auth_type: bearer
      api_token: your-oauth-token
      username: your-email@example.com
```

### Use Cases

- OAuth 2.0 applications
- Service account authentication
- Enterprise SSO integrations

## Attachment Management

Sophisticated attachment handling with version tracking.

### Hash-Based Versioning

Each attachment is tracked using SHA1 hash:

```
MKDocsWithConfluence [v{hash}]
```

### Update Logic

1. **Calculate Hash** - SHA1 of local file
2. **Check Existing** - Get attachment hash from Confluence
3. **Compare** - Only update if hash differs

### Status Messages

```
* Attachment: diagram.png - *NEW*        # First upload
* Attachment: diagram.png - *UPDATE*     # Content changed
* Attachment: diagram.png - *NO CHANGE*  # Hash matches
```

## Confluence-Specific Conversions

### Code Blocks

Markdown code blocks convert to Confluence code macros:

```python
def hello():
    print("Hello")
```

Becomes:

```xml
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[def hello():
    print("Hello")]]></ac:plain-text-body>
</ac:structured-macro>
```

### Tables

Markdown tables convert to Confluence table format with proper styling.

### Admonitions

MkDocs admonitions convert to Confluence info/warning/note macros.

## Rate Limiting and Retry

The plugin handles Confluence API limitations:

### Connection Errors

Automatically detects and logs:

- DNS resolution failures
- Connection refused errors
- Network timeouts

### Retry Logic

For newly created pages:

```python
wait_until(lambda: self.find_page_id(title),
           interval=1,
           timeout=20,
           max_retries=3)
```

Waits for Confluence to make pages available after creation.

## Advanced Logging

### Content Comparison

```
INFO - Content comparison for 'Getting Started':
INFO -   - Current: 1234 chars, New: 1250 chars
INFO -   - Debug files: /tmp/confluence-debug
INFO -     diff '/tmp/confluence-debug/Getting_Started_current_normalized.html' \
              '/tmp/confluence-debug/Getting_Started_new_normalized.html'
```

### Parent Chain Details

```
DEBUG - Resolving parent chain for page, found 3 ancestors
DEBUG - Added ancestor level 2: Getting Started
DEBUG - Added ancestor level 1: Guides
DEBUG - Final parent chain: ['Home', 'Guides', 'Getting Started']
```

## Performance Optimizations

### Parallel Processing

MkDocs processes pages in parallel during build.

### Skip Unchanged Pages

Smart comparison prevents unnecessary uploads:

```
Mkdocs With Confluence: Page 1 *UPDATE*
Mkdocs With Confluence: Page 2 *NO CHANGE*  ← Skipped
Mkdocs With Confluence: Page 3 *NO CHANGE*  ← Skipped
Mkdocs With Confluence: Page 4 *UPDATE*
```

### Minimal API Calls

Only makes API calls when necessary:
- Page creation/updates
- Attachment uploads
- Parent page lookups (cached)

## Next Steps

- [Managing Orphaned Pages](managing-orphaned-pages.md) - Keep your Confluence space synchronized
- [Dry Run Mode](dry-run.md) - Test locally before publishing
- [Configuration Reference](../reference/configuration.md) - All options
- [API Reference](../reference/SUMMARY.md) - Plugin internals
