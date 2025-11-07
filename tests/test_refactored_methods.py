"""Tests for refactored methods in MkdocsWithConfluence plugin."""

from unittest.mock import MagicMock, Mock

from mkdocs_to_confluence.plugin import MkdocsWithConfluence
from tests.fixtures.configs import CONFIG_DEBUG_MODE, MINIMAL_CONFIG


# ============================================================================
# Tests for _resolve_page_parents()
# ============================================================================


def test_resolve_page_parents_with_no_ancestors():
    """Test _resolve_page_parents() with no ancestors (top-level page)."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Mock page with no ancestors
    page = Mock()
    page.ancestors = []

    parent, parent1, main_parent = plugin._resolve_page_parents(page)

    assert parent == MINIMAL_CONFIG["parent_page_name"]
    assert parent1 == MINIMAL_CONFIG["parent_page_name"]
    assert main_parent == MINIMAL_CONFIG["parent_page_name"]


def test_resolve_page_parents_with_one_ancestor():
    """Test _resolve_page_parents() with one ancestor."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Mock page with one ancestor
    page = Mock()
    ancestor = Mock()
    ancestor.__repr__ = Mock(return_value="Section(title='Parent Section')")
    page.ancestors = [ancestor]

    parent, parent1, main_parent = plugin._resolve_page_parents(page)

    assert parent == "Parent Section"
    assert parent1 == MINIMAL_CONFIG["parent_page_name"]
    assert main_parent == MINIMAL_CONFIG["parent_page_name"]


def test_resolve_page_parents_with_multiple_ancestors():
    """Test _resolve_page_parents() with multiple ancestors."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Mock page with two ancestors
    page = Mock()
    ancestor1 = Mock()
    ancestor1.__repr__ = Mock(return_value="Section(title='Direct Parent')")
    ancestor2 = Mock()
    ancestor2.__repr__ = Mock(return_value="Section(title='Grandparent')")
    page.ancestors = [ancestor1, ancestor2]

    parent, parent1, main_parent = plugin._resolve_page_parents(page)

    assert parent == "Direct Parent"
    assert parent1 == "Grandparent"
    assert main_parent == MINIMAL_CONFIG["parent_page_name"]


def test_resolve_page_parents_uses_space_when_no_parent_page_name():
    """Test _resolve_page_parents() uses space as fallback when parent_page_name is None."""
    plugin = MkdocsWithConfluence()
    config = MINIMAL_CONFIG.copy()
    config["parent_page_name"] = None
    plugin.config = config

    page = Mock()
    page.ancestors = []

    parent, parent1, main_parent = plugin._resolve_page_parents(page)

    assert parent is None
    assert parent1 == MINIMAL_CONFIG["space"]
    assert main_parent == MINIMAL_CONFIG["space"]


# ============================================================================
# Tests for _extract_attachments()
# ============================================================================


def test_extract_attachments_file_protocol():
    """Test _extract_attachments() detects img src='file://...' format."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = '<img src="file:///tmp/image1.png" s'
    attachments = plugin._extract_attachments(markdown)

    assert "/tmp/image1.png" in attachments


def test_extract_attachments_markdown_format():
    """Test _extract_attachments() detects ![alt](path) format."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "![Screenshot](../images/screenshot.png)"
    attachments = plugin._extract_attachments(markdown)

    assert "images/screenshot.png" in attachments
    assert "docs/images/screenshot.png" in attachments


def test_extract_attachments_mixed_formats():
    """Test _extract_attachments() detects mixed formats."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = '''
    <img src="file:///tmp/temp_image.png" s
    ![Diagram](./diagrams/architecture.png)
    '''
    attachments = plugin._extract_attachments(markdown)

    assert "/tmp/temp_image.png" in attachments
    assert "diagrams/architecture.png" in attachments
    assert "docs/diagrams/architecture.png" in attachments


def test_extract_attachments_no_images():
    """Test _extract_attachments() handles markdown with no images."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "# Just a heading\n\nSome text content."
    attachments = plugin._extract_attachments(markdown)

    assert attachments == []


def test_extract_attachments_ignores_http_urls():
    """Test _extract_attachments() ignores http/https URLs."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "![External](https://example.com/image.png)"
    attachments = plugin._extract_attachments(markdown)

    # Should not include external URLs
    assert len(attachments) == 0


# ============================================================================
# Tests for _convert_to_confluence_format()
# ============================================================================


def test_convert_to_confluence_format_replaces_image_tags():
    """Test _convert_to_confluence_format() replaces image tags correctly."""
    from pathlib import Path

    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = '<img src="file:///tmp/test.png" style="page-break-inside: avoid;">'
    confluence_body, temp_path = plugin._convert_to_confluence_format(markdown, "TestPage")

    # Verify image tag was transformed
    assert '<img src="file:///tmp/' not in confluence_body
    assert 'ac:image' in confluence_body or '<p>' in confluence_body

    # Verify temp file exists and is not empty
    temp_file = Path(temp_path)
    assert temp_file.exists()
    assert temp_file.stat().st_size > 0

    # Verify copy file was created
    copy_file = Path("confluence_page_TestPage.html")
    assert copy_file.exists()

    # Cleanup
    temp_file.unlink()
    copy_file.unlink()


def test_convert_to_confluence_format_creates_temp_file():
    """Test _convert_to_confluence_format() creates temp file with content."""
    from pathlib import Path

    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "# Test Header\n\nTest content"
    confluence_body, temp_path = plugin._convert_to_confluence_format(markdown, "TestPage")

    # Verify return values
    assert isinstance(confluence_body, str)
    assert len(confluence_body) > 0
    assert isinstance(temp_path, str)

    # Verify temp file exists
    temp_file = Path(temp_path)
    assert temp_file.exists()
    assert temp_file.stat().st_size > 0

    # Cleanup
    temp_file.unlink()
    Path("confluence_page_TestPage.html").unlink(missing_ok=True)


def test_convert_to_confluence_format_handles_special_chars_in_page_name():
    """Test _convert_to_confluence_format() handles special characters in page names."""
    from pathlib import Path

    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "# Test"
    confluence_body, temp_path = plugin._convert_to_confluence_format(markdown, "Page With Spaces")

    # Verify copy file has underscores instead of spaces
    copy_file = Path("confluence_page_Page_With_Spaces.html")
    assert copy_file.exists()

    # Cleanup
    Path(temp_path).unlink()
    copy_file.unlink()
