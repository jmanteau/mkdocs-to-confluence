"""Export Confluence-formatted content to local filesystem in dry-run mode."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PageMetadata:
    """Metadata for a Confluence page export.

    Attributes:
        title: Page title
        parent: Direct parent page title
        space: Confluence space key
        attachments: List of attachment file paths
        confluence_body: The Confluence-formatted HTML content

    """

    title: str
    parent: str | None
    space: str
    attachments: list[str] = field(default_factory=list)
    confluence_body: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "parent": self.parent,
            "space": self.space,
            "attachments": self.attachments,
        }


class ConfluenceExporter:
    """Export Confluence-formatted pages to local filesystem.

    Creates a hierarchical directory structure that mirrors the Confluence
    page hierarchy, making it easy to review content before actual upload.
    """

    def __init__(self, export_dir: Path):
        """Initialize exporter with target directory.

        Args:
            export_dir: Root directory for exported content

        """
        self.export_dir = Path(export_dir)
        self.pages: dict[str, PageMetadata] = {}
        self.page_hierarchy: dict[str, list[str]] = {}

    def add_page(
        self,
        title: str,
        parent: str | None,
        space: str,
        confluence_body: str,
        attachments: list[str] | None = None,
    ) -> None:
        """Add a page to the export queue.

        Args:
            title: Page title
            parent: Direct parent page title (None for root pages)
            space: Confluence space key
            confluence_body: The Confluence-formatted HTML content
            attachments: Optional list of attachment file paths

        """
        metadata = PageMetadata(
            title=title,
            parent=parent,
            space=space,
            attachments=attachments or [],
            confluence_body=confluence_body,
        )
        self.pages[title] = metadata

        # Track hierarchy for directory structure
        if parent:
            if parent not in self.page_hierarchy:
                self.page_hierarchy[parent] = []
            self.page_hierarchy[parent].append(title)

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string to be safe for filesystem use.

        Args:
            name: The string to sanitize

        Returns:
            Sanitized string safe for use as filename/directory name

        """
        # First strip leading/trailing dots and spaces
        sanitized = name.strip(". ")

        # Replace problematic characters with underscores
        invalid_chars = '<>:"/\\|?* '
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")

        return sanitized or "unnamed"

    def _get_page_path(self, title: str, visited: set[str] | None = None) -> Path:
        """Get the directory path for a page based on its hierarchy.

        Args:
            title: Page title
            visited: Set of visited pages to detect cycles

        Returns:
            Path object representing the page's directory location

        """
        if visited is None:
            visited = set()

        metadata = self.pages.get(title)
        if not metadata or not metadata.parent:
            # Root page - goes directly under export_dir
            return self.export_dir / self._sanitize_filename(title)

        # Prevent infinite loops: if we're revisiting a page, place at root
        if title in visited:
            return self.export_dir / self._sanitize_filename(title)

        # If parent is already in chain, break cycle by returning export_dir
        # This prevents the calling page from being nested under this page
        if metadata.parent in visited:
            return self.export_dir

        visited.add(title)

        # Recursive: get parent path and append this page
        parent_path = self._get_page_path(metadata.parent, visited)
        return parent_path / self._sanitize_filename(title)

    def _export_page(self, title: str) -> None:
        """Export a single page with its content and attachments.

        Args:
            title: Page title to export

        """
        metadata = self.pages.get(title)
        if not metadata:
            return

        page_dir = self._get_page_path(title)
        page_dir.mkdir(parents=True, exist_ok=True)

        # Write Confluence HTML content
        html_file = page_dir / "page.html"
        html_file.write_text(metadata.confluence_body, encoding="utf-8")

        # Write page metadata
        metadata_file = page_dir / "metadata.json"
        metadata_file.write_text(
            json.dumps(metadata.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Copy attachments if any
        if metadata.attachments:
            attachments_dir = page_dir / "attachments"
            attachments_dir.mkdir(exist_ok=True)

            for attachment_path in metadata.attachments:
                src = Path(attachment_path)
                if src.exists() and src.is_file():
                    dst = attachments_dir / src.name
                    shutil.copy2(src, dst)

    def export_all(self) -> None:
        """Export all queued pages to the filesystem.

        Creates the complete directory structure and writes all pages,
        metadata, and attachments.
        """
        # Clean and create export directory
        if self.export_dir.exists():
            shutil.rmtree(self.export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Export each page
        for title in self.pages:
            self._export_page(title)

        # Write overall metadata summary
        summary = {
            "total_pages": len(self.pages),
            "pages": [
                {
                    "title": title,
                    "parent": metadata.parent,
                    "space": metadata.space,
                    "path": str(self._get_page_path(title).relative_to(self.export_dir)),
                }
                for title, metadata in self.pages.items()
            ],
        }

        metadata_file = self.export_dir / "metadata.json"
        metadata_file.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
