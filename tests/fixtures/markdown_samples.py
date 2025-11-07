"""Markdown content test fixtures."""

# Simple markdown without images
SIMPLE_MARKDOWN = """# Test Page

This is a simple test page with some content.

## Section 1

Some text here.
"""

# Markdown with file:// image reference
MARKDOWN_WITH_FILE_IMAGE = """# Test Page

![Test Image](file:///tmp/test_image.png)

Some content.
"""

# Markdown with relative path images
MARKDOWN_WITH_RELATIVE_IMAGES = """# Test Page

![Logo](../images/logo.png)

![Diagram](./diagrams/flow.png)

Some content.
"""

# Markdown with mixed image formats
MARKDOWN_WITH_MIXED_IMAGES = """# Test Page

<img src="file:///tmp/screenshot.png" style="page-break-inside: avoid;">

![Diagram](../images/diagram.png)

![Icon](./icons/home.png)
"""

# Markdown with no images
MARKDOWN_NO_IMAGES = """# Documentation

## Overview

This page contains only text content with no images or attachments.

- Item 1
- Item 2
- Item 3
"""

# Expected attachment lists
EXPECTED_ATTACHMENTS_FILE = [
    "/tmp/test_image.png",  # noqa: S108
]

EXPECTED_ATTACHMENTS_RELATIVE = [
    "images/logo.png",
    "docs/images/logo.png",
    "diagrams/flow.png",
    "docs/diagrams/flow.png",
]

EXPECTED_ATTACHMENTS_MIXED = [
    "/tmp/screenshot.png",  # noqa: S108
    "images/diagram.png",
    "docs/images/diagram.png",
    "icons/home.png",
    "docs/icons/home.png",
]
