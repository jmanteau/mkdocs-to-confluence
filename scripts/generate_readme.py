#!/usr/bin/env python3
"""Generate README.md from template and documentation sources.

This script uses a mapping configuration (docs/readme-mapping.yaml) to
extract sections from documentation files and render them into the README.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template


def extract_section(content: str, header: str, level: int = 2) -> str:
    """Extract content under a specific header.

    Args:
        content: The markdown content
        header: The header text to find
        level: Header level (2 for ##, 3 for ###, etc.)

    Returns:
        Content under the header until next same-level header

    """
    # Match the header and capture content until next header of same or higher level
    header_marker = "#" * level
    next_header_pattern = rf"^#{{1,{level}}}\s"

    # Find the header
    header_pattern = rf"^{re.escape(header_marker)}\s+{re.escape(header)}\s*$"
    lines = content.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        if re.match(header_pattern, line):
            start_idx = i + 1
            break

    if start_idx is None:
        return ""

    # Find the end (next header of same or higher level)
    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        if re.match(next_header_pattern, lines[i]):
            end_idx = i
            break

    section_content = "\n".join(lines[start_idx:end_idx]).strip()
    return section_content


def extract_content_after_frontmatter(content: str) -> str:
    """Remove frontmatter from markdown content.

    Args:
        content: Markdown content potentially with frontmatter

    Returns:
        Content without frontmatter

    """
    # Remove YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


def process_section_mapping(mapping: dict[str, Any], base_path: Path) -> str:
    """Process a single section mapping and extract content.

    Args:
        mapping: Section mapping configuration
        base_path: Base path for resolving relative file paths

    Returns:
        Extracted and processed content

    """
    file_path = base_path / mapping["file"]

    if not file_path.exists():
        sys.stderr.write(f"  ⚠ Warning: File not found: {file_path}\n")
        return ""

    # Read file content
    content = file_path.read_text()
    content = extract_content_after_frontmatter(content)

    # Extract specific section if specified
    if "section" in mapping:
        level = mapping.get("level", 2)
        content = extract_section(content, mapping["section"], level)

    # Add prefix if specified
    if "prefix" in mapping:
        content = mapping["prefix"] + content

    # Add suffix if specified
    if "suffix" in mapping:
        content = content + mapping["suffix"]

    return content


def load_mapping_config(config_path: Path) -> dict[str, Any]:
    """Load the README mapping configuration.

    Args:
        config_path: Path to the mapping YAML file

    Returns:
        Mapping configuration dictionary

    """
    with config_path.open() as f:
        return yaml.safe_load(f)


def extract_from_docs(mapping_config: dict[str, Any], base_path: Path) -> dict[str, str]:
    """Extract sections from documentation files based on mapping configuration.

    Args:
        mapping_config: Mapping configuration from YAML
        base_path: Project base path

    Returns:
        Dictionary with section names and their content

    """
    sections = {}

    for section_name, section_config in mapping_config.items():
        sys.stdout.write(f"  Processing section: {section_name}\n")

        # Handle multiple mappings for a single section
        if isinstance(section_config, list):
            combined_content = []
            for mapping in section_config:
                content = process_section_mapping(mapping, base_path)
                if content:
                    combined_content.append(content)
            sections[section_name] = "\n".join(combined_content)
        else:
            sections[section_name] = process_section_mapping(section_config, base_path)

        # Show preview
        if sections[section_name]:
            preview = sections[section_name][:50].replace("\n", " ")
            sys.stdout.write(f"    ✓ {preview}...\n")
        else:
            sys.stdout.write("    ⚠ No content extracted\n")

    return sections


def main() -> int:
    """Generate README.md from template."""
    sys.stdout.write("Generating README.md from template and docs...\n")

    # Project paths
    base_path = Path.cwd()
    template_file = base_path / "README.md.j2"
    mapping_file = base_path / "docs" / "readme-mapping.yaml"
    readme_file = base_path / "README.md"

    # Verify files exist
    if not template_file.exists():
        sys.stderr.write(f"Error: Template file {template_file} not found\n")
        return 1

    if not mapping_file.exists():
        sys.stderr.write(f"Error: Mapping file {mapping_file} not found\n")
        return 1

    # Load mapping configuration
    sys.stdout.write(f"Loading mapping configuration from {mapping_file.relative_to(base_path)}...\n")
    mapping_config = load_mapping_config(mapping_file)

    # Load template
    sys.stdout.write(f"Loading template from {template_file.relative_to(base_path)}...\n")
    template_content = template_file.read_text()
    template = Template(template_content)

    # Extract content from docs
    sys.stdout.write("Extracting sections from documentation...\n")
    sections = extract_from_docs(mapping_config, base_path)

    # Render template
    sys.stdout.write("Rendering template...\n")
    readme_content = template.render(**sections)

    # Write README.md
    readme_file.write_text(readme_content)
    sys.stdout.write(f"✓ Generated {readme_file.relative_to(base_path)}\n")

    return 0


if __name__ == "__main__":
    exit(main())
