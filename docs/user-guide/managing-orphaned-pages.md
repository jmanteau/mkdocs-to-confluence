# Managing Orphaned Pages

Learn how to handle Confluence pages that are no longer part of your documentation.

## What are Orphaned Pages?

Orphaned pages are pages that exist in Confluence but are no longer present in your MkDocs documentation. This happens when you:

- Rename or delete documentation files
- Reorganize your documentation structure
- Remove entire sections from your docs

The plugin doesn't delete these pages by default to prevent accidental data loss.

!!! note "Parent Pages Are Tracked"
    The plugin automatically tracks both regular pages **and** parent/section pages (navigation folders). Parent pages like "Tutorials", "How-To Guides", etc. are never marked as orphaned as long as they contain child pages in your documentation.

## Detecting Orphaned Pages

By default, mkdocs-to-confluence warns you about orphaned pages after each build:

```
WARNING: Found 3 orphaned page(s) in Confluence:
  - Old API Guide
  - Deprecated Features
  - Legacy Documentation
INFO: Run with 'cleanup_orphaned_pages: true' to delete them
```

This happens automatically - no configuration needed!

## Strategy 1: Track and Warn (Recommended)

The safest approach is to let the plugin warn you, then manually review and delete orphaned pages.

### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      # ... other config ...
      # No orphaned pages config needed - warnings are automatic
```

### Workflow

1. Run `mkdocs build`
2. Review warning messages about orphaned pages
3. Manually verify pages in Confluence
4. Delete unwanted pages through Confluence UI

**Pros:**
- Maximum safety
- Full control over deletion
- Time to review before removing content

**Cons:**
- Manual cleanup required
- Can accumulate stale pages over time

## Strategy 2: Automatic Cleanup

Enable automatic deletion of orphaned pages for hands-off management.

### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      cleanup_orphaned_pages: true  # Enable automatic cleanup
```

### What Happens

1. Plugin tracks all pages synced during build
2. After sync, fetches all pages from Confluence
3. Identifies pages in Confluence but not synced
4. Warns about orphaned pages (always logged)
5. Deletes orphaned pages automatically

**Pros:**
- Keeps Confluence clean automatically
- No manual intervention needed
- Documentation stays current

**Cons:**
- Permanently deletes pages
- Risk of accidental deletion
- No undo option

!!! warning "Test First"
    Always test with dry-run mode before enabling cleanup:
    ```yaml
    dryrun: true
    cleanup_orphaned_pages: true
    ```

## Strategy 3: Selective Preservation

Automatically clean up orphaned pages while preserving specific pages.

### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      cleanup_orphaned_pages: true
      keep_pages:
        - "Archive"
        - "Old Documentation"
        - "Manual Notes"
        - "Team Resources"
```

### Use Cases

- **Archives**: Keep old documentation for reference
- **Manual Pages**: Preserve hand-written content
- **Special Sections**: Protect pages created outside MkDocs
- **Shared Resources**: Keep pages used by multiple projects

**Pros:**
- Automatic cleanup with safety net
- Protect important manual content
- Flexibility for mixed documentation

## Strategy 4: Use Page Labels

Label auto-generated pages for easy identification and bulk management.

### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: DOCS
      page_label: auto-generated-docs  # Default value
```

### Confluence Workflow

1. All pages synced by the plugin get labeled
2. In Confluence, filter pages by label: `auto-generated-docs`
3. Manually identify and bulk-delete orphaned pages
4. Labels persist across updates

**Pros:**
- Easy to filter auto-generated pages in Confluence
- Bulk operations possible
- Visual identification
- No risk of accidental automation

**Cons:**
- Still requires manual deletion
- Need to use Confluence UI

## Recommended Workflows

### Development Environment

```yaml
# Safe defaults for development
plugins:
  - mkdocs-to-confluence:
      host_url: https://dev.atlassian.net/wiki/rest/api/content
      space: DEV
      cleanup_orphaned_pages: false  # Just warn
```

**Workflow:**
1. Make documentation changes
2. Run `mkdocs build`
3. Review warnings about orphaned pages
4. Test in Confluence
5. Manually clean up if needed

### Production Environment

```yaml
# Automatic cleanup in production
plugins:
  - mkdocs-to-confluence:
      host_url: https://company.atlassian.net/wiki/rest/api/content
      space: PROD
      cleanup_orphaned_pages: true
      keep_pages:
        - "Release Archive"
        - "Migration Notes"
      enabled_if_env: PUBLISH_TO_CONFLUENCE
```

**Workflow:**
1. Test in dev first
2. Enable via environment variable
3. CI/CD runs `mkdocs build`
4. Orphaned pages cleaned automatically
5. Protected pages preserved

### Migration/Reorganization

When reorganizing docs extensively:

```yaml
# Step 1: Dry run to see what would be deleted
plugins:
  - mkdocs-to-confluence:
      dryrun: true
      cleanup_orphaned_pages: true
```

Run and review logs, then:

```yaml
# Step 2: Protect pages you want to keep
plugins:
  - mkdocs-to-confluence:
      cleanup_orphaned_pages: true
      keep_pages:
        - "Important Archive Page"
        - "Legacy API Docs"
```

## Safety Tips

### Before Enabling Cleanup

1. **Backup Confluence space** using Confluence's export feature
2. **Test with dry-run** mode first:
   ```yaml
   dryrun: true
   cleanup_orphaned_pages: true
   ```
3. **Review logs** carefully for false positives
4. **Start with small changes** to build confidence

### Monitoring

Check plugin output after each build:

```
INFO: Mkdocs With Confluence: No orphaned pages found
```

Or:

```
WARNING: Found 2 orphaned page(s) in Confluence:
  - Old Tutorial
  - Removed Section
INFO: Mkdocs With Confluence: Cleanup enabled, deleting orphaned pages...
INFO: Deleted 2 orphaned page(s)
```

### Recovery

If a page is accidentally deleted:

1. Check Confluence trash/archive
2. Restore from Confluence UI
3. Add to `keep_pages` to prevent future deletion
4. Or recreate in MkDocs if it should be part of docs

## Common Scenarios

### Scenario: Renamed Documentation File

**What happens:**
- Old page name becomes orphaned
- New page is created
- Duplicate content in Confluence

**Solution with cleanup:**
```yaml
cleanup_orphaned_pages: true
```
Old page is automatically removed.

### Scenario: Reorganized Documentation Structure

**What happens:**
- Multiple pages may become orphaned
- New hierarchy created

**Solution:**
1. Enable cleanup
2. Use `keep_pages` for any manually-created pages
3. Run build and verify

### Scenario: Mixed Auto/Manual Documentation

**What happens:**
- Some pages created by plugin
- Some pages manually created in Confluence
- Manual pages show as "orphaned"

**Solution:**
```yaml
cleanup_orphaned_pages: true
keep_pages:
  - "Manual Page 1"
  - "Manual Page 2"
  - "Team Notes"
```

## FAQ

### Why are parent/folder pages not marked as orphaned?

Parent pages (like "Tutorials", "How-To Guides", "Reference") correspond to navigation sections in your mkdocs.yml. The plugin automatically tracks these pages during sync, so they're never incorrectly flagged as orphaned.

For example, with this navigation:

```yaml
nav:
  - Home: index.md
  - Tutorials:
      - Installation: tutorials/installation.md
      - Quick Start: tutorials/quick-start.md
```

The plugin tracks:
- "Home" (regular page)
- "Tutorials" (parent/section page)
- "Installation" (regular page)
- "Quick Start" (regular page)

All four pages are considered "synced" and won't be marked as orphaned.

### What if I have an empty parent section?

If you remove all child pages from a section but keep the section in your navigation, the parent page will still be tracked and won't be marked as orphaned. To remove the parent page:

1. Remove the entire section from mkdocs.yml nav
2. Run `mkdocs build`
3. The parent page will now be detected as orphaned

### Can I protect specific parent pages?

Yes, use the `keep_pages` option:

```yaml
cleanup_orphaned_pages: true
keep_pages:
  - "Old Tutorials"  # Keeps this parent and all its children
  - "Archive"
```

## Next Steps

- [Configuration Reference](../reference/configuration.md) - All configuration options
- [Advanced Features](advanced-features.md) - Other plugin capabilities
- [Troubleshooting](../troubleshooting.md) - Common issues and solutions
