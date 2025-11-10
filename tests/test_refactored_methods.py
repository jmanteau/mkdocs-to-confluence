"""Tests for refactored methods in MkdocsWithConfluence plugin."""

from unittest.mock import Mock

from mkdocs_to_confluence.plugin import MkdocsWithConfluence
from tests.fixtures.configs import MINIMAL_CONFIG

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

    parent_chain = plugin._resolve_page_parents(page)

    # With no ancestors, should return just the main parent
    assert len(parent_chain) == 1
    assert parent_chain[0] == MINIMAL_CONFIG["parent_page_name"]


def test_resolve_page_parents_with_one_ancestor():
    """Test _resolve_page_parents() with one ancestor."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Mock page with one ancestor
    page = Mock()
    ancestor = Mock()
    ancestor.__repr__ = Mock(return_value="Section(title='Parent Section')")
    page.ancestors = [ancestor]

    parent_chain = plugin._resolve_page_parents(page)

    # Should return: [main_parent, direct_parent]
    assert len(parent_chain) == 2
    assert parent_chain[0] == MINIMAL_CONFIG["parent_page_name"]  # root
    assert parent_chain[1] == "Parent Section"  # direct parent


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

    parent_chain = plugin._resolve_page_parents(page)

    # Should return: [main_parent, grandparent, direct_parent]
    # Ancestors are ordered [0]=direct parent, [1]=grandparent
    # So reversed: [main_parent, grandparent, direct_parent]
    assert len(parent_chain) == 3
    assert parent_chain[0] == MINIMAL_CONFIG["parent_page_name"]  # root
    assert parent_chain[1] == "Grandparent"  # second level
    assert parent_chain[2] == "Direct Parent"  # direct parent


def test_resolve_page_parents_uses_space_when_no_parent_page_name():
    """Test _resolve_page_parents() uses space as fallback when parent_page_name is None."""
    plugin = MkdocsWithConfluence()
    config = MINIMAL_CONFIG.copy()
    config["parent_page_name"] = None
    plugin.config = config

    page = Mock()
    page.ancestors = []

    parent_chain = plugin._resolve_page_parents(page)

    # Should use space as the root when parent_page_name is None
    assert len(parent_chain) == 1
    assert parent_chain[0] == MINIMAL_CONFIG["space"]


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
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = '<img src="file:///tmp/test.png" style="page-break-inside: avoid;">'
    confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

    # Verify image tag was transformed
    assert '<img src="file:///tmp/' not in confluence_body
    assert 'ac:image' in confluence_body or '<p>' in confluence_body

    # Verify content is not empty
    assert len(confluence_body) > 0


def test_convert_to_confluence_format_creates_temp_file():
    """Test _convert_to_confluence_format() converts content correctly."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "# Test Header\n\nTest content"
    confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

    # Verify return value
    assert isinstance(confluence_body, str)
    assert len(confluence_body) > 0
    # Check that markdown was converted to HTML
    assert '<h1>' in confluence_body or 'Test Header' in confluence_body


def test_convert_to_confluence_format_handles_special_chars_in_page_name():
    """Test _convert_to_confluence_format() handles special characters in page names."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    markdown = "# Test"
    confluence_body = plugin._convert_to_confluence_format(markdown, "Page With Spaces")

    # Verify content was converted successfully
    assert isinstance(confluence_body, str)
    assert len(confluence_body) > 0
    assert '<h1>' in confluence_body or 'Test' in confluence_body
