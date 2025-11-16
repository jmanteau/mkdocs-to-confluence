# Troubleshooting

Common issues and solutions for mkdocs-to-confluence.

## Authentication Issues

### Authentication Failed

**Symptoms:**
- `401 Unauthorized` error
- `Authentication failed` message

**Solutions:**

1. **Verify Credentials**
   ```bash
   # Check environment variables
   echo $JIRA_USERNAME
   echo $CONFLUENCE_API_TOKEN
   ```

2. **Check Username Format**
   - **Confluence Cloud**: Use email address (e.g., `user@example.com`)
   - **Confluence Server**: Use username (e.g., `jsmith`)

3. **Verify API Token**
   - Generate new token at https://id.atlassian.com/manage-profile/security/api-tokens
   - Ensure token hasn't expired
   - Check token has correct permissions

4. **Test Authentication**
   ```bash
   curl -u "email@example.com:api-token" \
     https://your-domain.atlassian.net/wiki/rest/api/space
   ```

### API Token Not Working

**Issue:** Token authentication fails

**Solutions:**

1. Use HTTP Basic Auth with API token:
   ```yaml
   plugins:
     - mkdocs-to-confluence:
         auth_type: basic  # Not 'bearer'
         username: email@example.com
         api_token: your-token
   ```

2. Check `auth_type` setting:
   - `basic` - For API tokens (default)
   - `bearer` - For OAuth tokens only

## Connection Issues

### Cannot Connect to Confluence

**Symptoms:**
- `DNS resolution failed`
- `Connection refused`
- Network timeout

**Solutions:**

1. **Verify URL Format**
   ```yaml
   # Correct format for Confluence Cloud:
   host_url: https://your-domain.atlassian.net/wiki/rest/api/content

   # Not:
   host_url: https://your-domain.atlassian.net  # ❌ Missing path
   ```

2. **Check Network Access**
   ```bash
   # Test connectivity
   curl https://your-domain.atlassian.net/wiki/rest/api/space
   ```

3. **Firewall/VPN Issues**
   - Check if VPN is required
   - Verify firewall allows HTTPS (443)
   - Test from same network as CI/CD

4. **Proxy Configuration**
   ```bash
   export HTTP_PROXY=http://proxy:port
   export HTTPS_PROXY=http://proxy:port
   ```

## Space and Page Issues

### Space Not Found

**Symptoms:**
- `Space 'XXX' not found`
- `404 Not Found` error

**Solutions:**

1. **Verify Space Key**
   - Space key is case-sensitive
   - Find in URL: `https://.../wiki/spaces/SPACEKEY/`
   - Or in Confluence: Space Settings → Overview

2. **Check Permissions**
   ```bash
   # Test space access
   curl -u "email:token" \
     https://your-domain.atlassian.net/wiki/rest/api/space/SPACEKEY
   ```

3. **Verify Account Access**
   - Log into Confluence web UI
   - Navigate to the space
   - Confirm you can view/edit pages

### Parent Page Not Found

**Symptoms:**
- `Parent page 'Title' not found`
- Pages created at wrong location

**Solutions:**

1. **Create Parent Page First**
   - Manually create parent page in Confluence
   - Or set `parent_page_name` to existing page

2. **Verify Exact Title**
   ```yaml
   # Title must match exactly (case-sensitive)
   parent_page_name: "API Documentation"  # Not "api documentation"
   ```

3. **Check Page Permissions**
   - Ensure you can edit the parent page
   - Verify page isn't restricted

4. **Use Space as Parent**
   ```yaml
   # Omit parent_page_name to use space root
   plugins:
     - mkdocs-to-confluence:
         space: DOCS
         # No parent_page_name - creates at space root
   ```

### Page Already Exists

**Symptoms:**
- Duplicate pages created
- "Page with this title already exists" error

**Solutions:**

1. **Check for Duplicates**
   - Search Confluence for existing page
   - Delete duplicates manually
   - Ensure unique page titles

2. **Review Navigation**
   ```yaml
   nav:
     - Getting Started: start.md
     - Getting Started: intro.md  # ❌ Duplicate title
   ```

3. **Enable Debug Mode**
   ```yaml
   debug: true
   ```
   Check logs for page ID resolution

## Image and Attachment Issues

### Images Not Uploading

**Symptoms:**
- Images missing in Confluence
- Broken image links

**Solutions:**

1. **Verify Image Paths**
   ```markdown
   # Correct - relative to docs/
   ![Diagram](images/diagram.png)

   # Incorrect - absolute path
   ![Diagram](/absolute/path/diagram.png)  # ❌
   ```

2. **Check File Exists**
   ```bash
   ls docs/images/diagram.png
   ```

3. **Supported Formats**
   - PNG, JPG, JPEG, GIF
   - SVG (check Confluence version)
   - PDF (as attachments)

4. **File Size Limits**
   - Confluence has file size limits (typically 100MB)
   - Compress large images

5. **Debug Attachment Process**
   ```yaml
   debug: true
   ```
   Look for attachment upload messages

### Attachments Not Updating

**Symptoms:**
- Old image versions in Confluence
- Changes not reflected

**Solutions:**

1. **Check Hash Updates**
   - Plugin uses SHA1 hash to track changes
   - Look for log: `Attachment: file.png - *UPDATE*`

2. **Clear Confluence Cache**
   - Confluence may cache images
   - Hard refresh browser (Ctrl+F5)

3. **Force Re-upload**
   - Delete attachment in Confluence
   - Rebuild documentation

## Build and Sync Issues

### Pages Not Syncing

**Symptoms:**
- Build succeeds but pages missing
- No changes in Confluence

**Solutions:**

1. **Check Plugin Enabled**
   ```yaml
   plugins:
     - search
     - mkdocs-to-confluence:  # Must be listed
   ```

2. **Verify Environment Variable**
   ```yaml
   enabled_if_env: PUBLISH_TO_CONFLUENCE
   ```
   ```bash
   # Check it's set
   echo $PUBLISH_TO_CONFLUENCE  # Should be "1"
   ```

3. **Check Dry Run Mode**
   ```yaml
   dryrun: false  # Must be false to publish
   ```

4. **Review Build Logs**
   ```bash
   mkdocs build --verbose
   ```

### Content Not Updating

**Symptoms:**
- Build shows `*NO CHANGE*`
- Content appears different

**Solutions:**

1. **Check Normalized Comparison**
   - Plugin normalizes content before comparison
   - Enable debug_diff mode to see content comparison:
   ```yaml
   debug_diff: true  # Shows detailed content comparison and creates diff files
   ```

2. **Review Debug Files**
   ```bash
   ls /tmp/confluence-debug/
   diff /tmp/confluence-debug/Page_current_normalized.html \
        /tmp/confluence-debug/Page_new_normalized.html
   ```

3. **Force Update**
   - Delete page in Confluence
   - Rebuild documentation

### Build Hangs or Times Out

**Symptoms:**
- Build process hangs
- Timeout errors

**Solutions:**

1. **Check Rate Limiting**
   - Confluence may rate-limit API calls
   - Add delays between requests

2. **Reduce Page Count**
   - Build smaller sets of pages
   - Use conditional publishing

3. **Check Network Stability**
   - Verify consistent connectivity
   - Test with smaller builds

4. **Increase Timeout**
   ```python
   # Custom timeout in plugin (advanced)
   timeout=300  # 5 minutes
   ```

## Permission Issues

### Permission Denied

**Symptoms:**
- `403 Forbidden` error
- "You don't have permission" message

**Solutions:**

1. **Verify Space Permissions**
   - Log into Confluence
   - Navigate to Space Settings → Permissions
   - Ensure account has "Add Pages" permission

2. **Check Page Restrictions**
   - Parent page may have restrictions
   - View page → Restrictions
   - Add your account to allowed users/groups

3. **Admin Rights**
   - Some operations require admin rights
   - Contact Confluence administrator

4. **API Token Scope**
   - Ensure token has write permissions
   - Regenerate token with correct scopes

## Debugging Strategies

### Enable Debug Logging

```yaml
plugins:
  - mkdocs-to-confluence:
      debug: true        # General debug info (API calls, parent chain, etc.)
      debug_diff: true   # Detailed content comparison (creates temp files)
      verbose: true
```

**Output includes:**
- `debug`: API request/response details, parent chain resolution, attachment processing
- `debug_diff`: Content comparison details, normalized diff files, character counts

### Use Dry Run Mode

```yaml
plugins:
  - mkdocs-to-confluence:
      dryrun: true
      export_dir: confluence-export
```

**Benefits:**
- Preview converted HTML
- Verify page hierarchy
- Check attachment paths
- Test without publishing

### Check Debug Files

```bash
# Content comparison
ls /tmp/confluence-debug/

# View normalized content
cat /tmp/confluence-debug/Page_Title_current_normalized.html
cat /tmp/confluence-debug/Page_Title_new_normalized.html

# Compare
diff /tmp/confluence-debug/Page_Title_current_normalized.html \
     /tmp/confluence-debug/Page_Title_new_normalized.html
```

### Test API Access

```bash
# Test authentication
curl -u "email:token" \
  https://your-domain.atlassian.net/wiki/rest/api/space

# Test space access
curl -u "email:token" \
  https://your-domain.atlassian.net/wiki/rest/api/space/SPACEKEY

# Test page creation
curl -u "email:token" -X POST \
  -H "Content-Type: application/json" \
  -d '{"type":"page","title":"Test","space":{"key":"SPACEKEY"},"body":{"storage":{"value":"<p>Test</p>","representation":"storage"}}}' \
  https://your-domain.atlassian.net/wiki/rest/api/content
```

## Getting Help

If you're still stuck:

1. **Check Logs Carefully**
   - Enable debug mode
   - Look for specific error messages
   - Note line numbers and context

2. **Search Existing Issues**
   - [GitHub Issues](https://github.com/jmanteau/mkdocs-to-confluence/issues)
   - Check closed issues too

3. **Create Minimal Reproduction**
   - Simplify configuration
   - Test with minimal docs
   - Isolate the problem

4. **Report Issue**
   - Include configuration (redact credentials!)
   - Include error messages
   - Include debug output
   - Include MkDocs/Python versions

## Common Error Messages

### "YOU HAVE EMPTY VALUES IN YOUR CONFIG"

**Cause:** Required configuration parameters missing

**Solution:** Verify all required fields:
```yaml
host_url: <must be set>
space: <must be set>
username: <must be set or env var>
api_token: <must be set or env var>
```

### "ROOT PARENT 'XXX' UNKNOWN. ABORTING!"

**Cause:** Parent page specified in config doesn't exist

**Solution:**
- Create the parent page in Confluence first
- Or remove `parent_page_name` to use space root

### "PAGE DOES NOT EXIST YET!"

**Cause:** Trying to update non-existent page (internal error)

**Solution:** Should auto-create. If persistent, report bug.

### "HTTP error on adding page"

**Cause:** Parent page not yet synced to Confluence

**Solution:** Plugin will retry automatically. If fails, check logs.

## Next Steps

- [Configuration Reference](getting-started/configuration.md) - Review all options
- [Basic Usage](user-guide/basic-usage.md) - Understand workflow
- [Contributing](contributing.md) - Report bugs or contribute fixes
