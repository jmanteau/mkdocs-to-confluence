---
title: Troubleshooting for README
---

### Common Issues

For detailed troubleshooting, see the [full documentation](https://jmanteau.github.io/mkdocs-to-confluence/troubleshooting/).

**Quick fixes:**
- **Authentication failed**: Verify username and API token
- **Space not found**: Check space key (case-sensitive)
- **Parent page not found**: Create parent page in Confluence first
- **Images not uploading**: Check image paths in Markdown

**Debug mode:**

```yaml
plugins:
  - mkdocs-to-confluence:
      debug: true
      verbose: true
```

**Dry run testing:**

```yaml
plugins:
  - mkdocs-to-confluence:
      dryrun: true
      export_dir: confluence-export
```
