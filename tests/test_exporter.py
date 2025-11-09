"""Tests for Confluence exporter functionality."""

from __future__ import annotations

import json
from pathlib import Path

from mkdocs_to_confluence.exporter import ConfluenceExporter, PageMetadata


def test_page_metadata_to_dict():
    """Test PageMetadata converts to dictionary correctly."""
    metadata = PageMetadata(
        title="Test Page",
        parent="Parent Page",
        space="TEST",
        attachments=["image.png"],
        confluence_body="<p>Content</p>",
    )

    result = metadata.to_dict()

    assert result["title"] == "Test Page"
    assert result["parent"] == "Parent Page"
    assert result["space"] == "TEST"
    assert result["attachments"] == ["image.png"]
    assert "confluence_body" not in result


def test_exporter_initialization(tmp_path):
    """Test ConfluenceExporter initializes correctly."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    assert exporter.export_dir == export_dir
    assert exporter.pages == {}
    assert exporter.page_hierarchy == {}


def test_add_page_no_parent():
    """Test adding a root page without parent."""
    exporter = ConfluenceExporter(Path("/tmp/test"))  # noqa: S108

    exporter.add_page(
        title="Root Page",
        parent=None,
        space="TEST",
        confluence_body="<p>Root content</p>",
    )

    assert "Root Page" in exporter.pages
    metadata = exporter.pages["Root Page"]
    assert metadata.title == "Root Page"
    assert metadata.parent is None
    assert metadata.space == "TEST"
    assert metadata.confluence_body == "<p>Root content</p>"


def test_add_page_with_parent():
    """Test adding a child page with parent."""
    exporter = ConfluenceExporter(Path("/tmp/test"))  # noqa: S108

    exporter.add_page(
        title="Parent Page",
        parent=None,
        space="TEST",
        confluence_body="<p>Parent</p>",
    )
    exporter.add_page(
        title="Child Page",
        parent="Parent Page",
        space="TEST",
        confluence_body="<p>Child</p>",
    )

    assert "Child Page" in exporter.pages
    assert "Parent Page" in exporter.page_hierarchy
    assert "Child Page" in exporter.page_hierarchy["Parent Page"]


def test_add_page_with_attachments():
    """Test adding a page with attachments."""
    exporter = ConfluenceExporter(Path("/tmp/test"))  # noqa: S108
    attachments = ["image1.png", "doc.pdf"]

    exporter.add_page(
        title="Page With Files",
        parent=None,
        space="TEST",
        confluence_body="<p>Content</p>",
        attachments=attachments,
    )

    metadata = exporter.pages["Page With Files"]
    assert metadata.attachments == attachments


def test_sanitize_filename():
    """Test filename sanitization removes invalid characters."""
    exporter = ConfluenceExporter(Path("/tmp/test"))  # noqa: S108

    assert exporter._sanitize_filename("Normal Name") == "Normal_Name"
    assert exporter._sanitize_filename("Name/With\\Slashes") == "Name_With_Slashes"
    assert exporter._sanitize_filename('Name<>:"|?*') == "Name_______"
    assert exporter._sanitize_filename("  .Name.  ") == "Name"
    assert exporter._sanitize_filename("...") == "unnamed"


def test_get_page_path_root_page(tmp_path):
    """Test getting path for root page."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    exporter.add_page(
        title="Root Page",
        parent=None,
        space="TEST",
        confluence_body="<p>Content</p>",
    )

    path = exporter._get_page_path("Root Page")
    assert path == export_dir / "Root_Page"


def test_get_page_path_nested_page(tmp_path):
    """Test getting path for nested child page."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    exporter.add_page("Root", None, "TEST", "<p>Root</p>")
    exporter.add_page("Parent", "Root", "TEST", "<p>Parent</p>")
    exporter.add_page("Child", "Parent", "TEST", "<p>Child</p>")

    path = exporter._get_page_path("Child")
    assert path == export_dir / "Root" / "Parent" / "Child"


def test_get_page_path_prevents_cycles(tmp_path):
    """Test circular reference detection prevents infinite loops."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    # Create circular reference
    exporter.pages["Page A"] = PageMetadata("Page A", "Page B", "TEST", [], "<p>A</p>")
    exporter.pages["Page B"] = PageMetadata("Page B", "Page A", "TEST", [], "<p>B</p>")

    # Should not raise exception
    path = exporter._get_page_path("Page A")
    assert path == export_dir / "Page_A"


def test_export_page_creates_structure(tmp_path):
    """Test exporting a single page creates correct file structure."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    exporter.add_page(
        title="Test Page",
        parent=None,
        space="TEST",
        confluence_body="<p>Test content</p>",
    )

    exporter._export_page("Test Page")

    page_dir = export_dir / "Test_Page"
    assert page_dir.exists()
    assert (page_dir / "page.html").exists()
    assert (page_dir / "metadata.json").exists()

    # Check HTML content
    html_content = (page_dir / "page.html").read_text()
    assert html_content == "<p>Test content</p>"

    # Check metadata
    metadata_content = json.loads((page_dir / "metadata.json").read_text())
    assert metadata_content["title"] == "Test Page"
    assert metadata_content["space"] == "TEST"


def test_export_page_with_attachments(tmp_path):
    """Test exporting a page with attachments copies files."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    # Create a test attachment file
    attachment_file = tmp_path / "test_image.png"
    attachment_file.write_text("fake image data")

    exporter.add_page(
        title="Page With Attachment",
        parent=None,
        space="TEST",
        confluence_body="<p>Content</p>",
        attachments=[str(attachment_file)],
    )

    exporter._export_page("Page With Attachment")

    page_dir = export_dir / "Page_With_Attachment"
    attachments_dir = page_dir / "attachments"
    assert attachments_dir.exists()
    assert (attachments_dir / "test_image.png").exists()
    assert (attachments_dir / "test_image.png").read_text() == "fake image data"


def test_export_page_missing_attachment(tmp_path):
    """Test exporting page with missing attachment does not fail."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    exporter.add_page(
        title="Page With Missing",
        parent=None,
        space="TEST",
        confluence_body="<p>Content</p>",
        attachments=["/nonexistent/file.png"],
    )

    # Should not raise exception
    exporter._export_page("Page With Missing")

    page_dir = export_dir / "Page_With_Missing"
    assert page_dir.exists()


def test_export_all_creates_complete_structure(tmp_path):
    """Test export_all creates complete directory structure."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    # Create hierarchy: Root -> Parent -> Child
    exporter.add_page("Root", None, "TEST", "<p>Root</p>")
    exporter.add_page("Parent", "Root", "TEST", "<p>Parent</p>")
    exporter.add_page("Child", "Parent", "TEST", "<p>Child</p>")
    exporter.add_page("Another Root", None, "TEST", "<p>Another</p>")

    exporter.export_all()

    # Check structure exists
    assert export_dir.exists()
    assert (export_dir / "Root").exists()
    assert (export_dir / "Root" / "Parent").exists()
    assert (export_dir / "Root" / "Parent" / "Child").exists()
    assert (export_dir / "Another_Root").exists()

    # Check overall metadata
    metadata = json.loads((export_dir / "metadata.json").read_text())
    assert metadata["total_pages"] == 4
    assert len(metadata["pages"]) == 4


def test_export_all_cleans_existing_directory(tmp_path):
    """Test export_all removes existing export directory."""
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    (export_dir / "old_file.txt").write_text("old content")

    exporter = ConfluenceExporter(export_dir)
    exporter.add_page("New Page", None, "TEST", "<p>New</p>")

    exporter.export_all()

    assert export_dir.exists()
    assert not (export_dir / "old_file.txt").exists()
    assert (export_dir / "New_Page").exists()


def test_export_all_with_unicode_content(tmp_path):
    """Test exporting pages with unicode characters."""
    export_dir = tmp_path / "export"
    exporter = ConfluenceExporter(export_dir)

    exporter.add_page(
        title="Unicode Page 中文",
        parent=None,
        space="TEST",
        confluence_body="<p>Content with émojis 🎉</p>",
    )

    exporter.export_all()

    page_dir = export_dir / "Unicode_Page_中文"
    assert page_dir.exists()

    html_content = (page_dir / "page.html").read_text(encoding="utf-8")
    assert "émojis 🎉" in html_content
