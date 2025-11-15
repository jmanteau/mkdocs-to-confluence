# README Generation System

This directory contains content sections specifically for the README.md file generation.

## Overview

The `scripts/generate_readme.py` script uses markdown-analysis to extract content from documentation files and generate the README.md. All mappings are configured in `docs/readme-mapping.yaml`.

## Architecture

1. **Mapping Configuration**: `docs/readme-mapping.yaml` defines which docs sections map to README sections
2. **Content Sources**: All content lives in `docs/` directory
3. **Generation Script**: `scripts/generate_readme.py` extracts and combines content
4. **Template**: `README.md.j2` defines the README structure with placeholders

## Content Mapping Table

| README Section | Source File | Section Extracted | Notes |
|----------------|-------------|-------------------|-------|
| **Features** | `docs/index.md` | "Features" (level 2) | Main feature highlights |
| **Installation** | `docs/getting-started/installation.md` | "Install from PyPI" (level 2) | Basic installation steps |
| **Quick Start** | `docs/getting-started/quick-start.md` | "Step 2: Get Confluence Credentials" (level 2) | Quick setup guide |
| **Configuration** | `docs/getting-started/configuration.md` | "Basic Configuration" + "Authentication" (level 2) | Combined sections |
| **Usage Examples** | `docs/user-guide/basic-usage.md` | "Basic Workflow" (level 2) | Basic usage patterns |
| **Markdown Support** | `docs/readme-sections/markdown-support.md` | Entire content (no section) | Markdown feature summary |
| **Troubleshooting** | `docs/readme-sections/troubleshooting.md` | Entire content (no section) | Quick troubleshooting tips |
| **Contributing** | `docs/readme-sections/contributing.md` | Entire content (no section) | Quick start for contributors |

## Directory Structure

```
docs/
├── readme-mapping.yaml           # Mapping configuration
├── readme-sections/              # README-specific content
│   ├── markdown-support.md      # Markdown features for README
│   ├── troubleshooting.md       # Quick troubleshooting for README
│   └── contributing.md          # Quick contributing guide for README
├── getting-started/              # Main docs (also used in README)
│   ├── installation.md
│   ├── quick-start.md
│   └── configuration.md
├── user-guide/                   # Main docs (also used in README)
│   ├── basic-usage.md
│   └── advanced-features.md
└── index.md                      # Main docs index (features extracted)
```

## How to Update README Content

1. **Edit the source content** in the appropriate docs file (see mapping table above)
2. **Run the generation script**:
   ```bash
   make readme
   # or
   uv --native-tls run python scripts/generate_readme.py
   ```
3. **Review the generated README.md**
4. **Commit both the docs and generated README**

## Configuration Format

The `docs/readme-mapping.yaml` supports:

```yaml
section_name:
  file: docs/path/to/file.md          # Source file
  section: "Header Name"              # Optional: specific section to extract
  level: 2                            # Optional: header level (default 2)
  prefix: "### Title\n\n"            # Optional: text to add before
  suffix: "\n\nExtra text"           # Optional: text to add after
```

### Multiple Sources

To combine multiple sections into one README section:

```yaml
section_name:
  - file: docs/file1.md
    section: "Section 1"
  - file: docs/file2.md
    section: "Section 2"
```

## Benefits of This Approach

1. **Single Source of Truth**: Content lives in docs, not in scripts
2. **Clear Mapping**: YAML configuration shows exactly what goes where
3. **Easy Maintenance**: Update docs in one place, README updates automatically
4. **Flexibility**: Can extract specific sections or entire files
5. **Composability**: Can combine multiple sources into one README section
6. **Reusability**: Markdown analysis functions are generic and reusable

## Markdown Analysis Functions

The script provides these utilities:

- `extract_section(content, header, level)`: Extract content under a specific header
- `extract_content_after_frontmatter(content)`: Remove YAML frontmatter
- `process_section_mapping(mapping, base_path)`: Process one mapping entry
- `load_mapping_config(config_path)`: Load YAML configuration
- `extract_from_docs(mapping_config, base_path)`: Extract all sections

These functions can be reused for other documentation generation tasks.
