---
title: Markdown Support for README
---

### H1 Heading Strip

Remove redundant H1 headings from your pages since Confluence displays the page title.

#### Configuration

```yaml
plugins:
  - mkdocs-to-confluence:
      strip_h1: true
```

#### Behavior

**Before:**
```markdown
# Page Title
## Section
```

**After sync to Confluence:**
```markdown
## Section
```

For more Markdown features, see the [Markdown Showcase](../markdown-showcase.md) and [full documentation](https://jmanteau.github.io/mkdocs-to-confluence/).
