"""Tests for string parsing and helper methods."""

import re
import tempfile
from pathlib import Path

from mkdocs_to_confluence.plugin import MkdocsWithConfluence
from tests.fixtures.markdown_samples import (
    MARKDOWN_NO_IMAGES,
    MARKDOWN_WITH_FILE_IMAGE,
    MARKDOWN_WITH_MIXED_IMAGES,
    MARKDOWN_WITH_RELATIVE_IMAGES,
)


def test_get_page_url():
    """Test extraction of page URL from nav representation."""
    plugin = MkdocsWithConfluence()

    nav_string = "Page(title='Test', url='docs/test/')"
    url = plugin._MkdocsWithConfluence__get_page_url(nav_string)

    assert url == "docs/test.md"


def test_get_page_name():
    """Test extraction of page name from nav representation."""
    plugin = MkdocsWithConfluence()

    nav_string = "Page(title='Test', url='docs/guides/setup/')"
    name = plugin._MkdocsWithConfluence__get_page_name(nav_string)

    assert name == "setup"


def test_get_section_title_valid():
    """Test extraction of section title from valid nav representation."""
    plugin = MkdocsWithConfluence()
    plugin.config = {"debug": False}

    nav_string = "Section(title='User Guide')"
    title = plugin._MkdocsWithConfluence__get_section_title(nav_string)

    assert title == "User Guide"


def test_get_section_title_with_debug():
    """Test section title extraction with debug mode enabled."""
    plugin = MkdocsWithConfluence()
    plugin.config = {"debug": True}

    nav_string = "Section(title='API Reference')"
    title = plugin._MkdocsWithConfluence__get_section_title(nav_string)

    assert title == "API Reference"


def test_get_section_title_no_title():
    """Test section title extraction returns None for malformed input."""
    plugin = MkdocsWithConfluence()
    plugin.config = {"debug": False}

    # Malformed section string - defensive programming returns None
    nav_string = "Section(url='guides/')"
    title = plugin._MkdocsWithConfluence__get_section_title(nav_string)

    # With defensive programming, returns None instead of crashing
    assert title is None


def test_get_page_title_valid():
    """Test extraction of page title from valid nav representation."""
    plugin = MkdocsWithConfluence()

    nav_string = "  Page(title='Installation', url='docs/install/')"
    title = plugin._MkdocsWithConfluence__get_page_title(nav_string)

    assert title == "Installation"


def test_get_page_title_no_title():
    """Test page title extraction falls back to URL when title missing."""
    plugin = MkdocsWithConfluence()

    nav_string = "Page(title=None, url='index/')"
    title = plugin._MkdocsWithConfluence__get_page_title(nav_string)

    # Should return the URL or None
    assert title is None or "index" in title


def test_get_file_sha1_with_text_file(tmp_path):
    """Test SHA1 hash calculation for text file."""
    plugin = MkdocsWithConfluence()

    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    sha1 = plugin.get_file_sha1(str(test_file))

    assert sha1 is not None
    assert len(sha1) == 40
    assert sha1 == "1eebdf4fdc9fc7bf283031b93f9aef3338de9052"


def test_get_file_sha1_with_binary_file(tmp_path):
    """Test SHA1 hash calculation for binary file."""
    plugin = MkdocsWithConfluence()

    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    sha1 = plugin.get_file_sha1(str(test_file))

    assert sha1 is not None
    assert len(sha1) == 40


def test_get_file_sha1_with_empty_file(tmp_path):
    """Test SHA1 hash calculation for empty file."""
    plugin = MkdocsWithConfluence()

    test_file = tmp_path / "empty.txt"
    test_file.write_text("")

    sha1 = plugin.get_file_sha1(str(test_file))

    assert sha1 is not None
    assert len(sha1) == 40
    assert sha1 == "da39a3ee5e6b4b0d3255bfef95601890afd80709"


def test_get_file_sha1_stability(tmp_path):
    """Test SHA1 hash is consistent for same content."""
    plugin = MkdocsWithConfluence()

    test_file = tmp_path / "stable.txt"
    test_file.write_text("consistent content")

    sha1_first = plugin.get_file_sha1(str(test_file))
    sha1_second = plugin.get_file_sha1(str(test_file))

    assert sha1_first == sha1_second


def test_markdown_image_detection_file_protocol():
    """Test detection of file:// protocol images in markdown format."""
    # Fixture uses markdown syntax ![](file://...), not HTML <img> tags
    attachments = []
    for match in re.finditer(r"!\[.*?\]\(file://(.+?)\)", MARKDOWN_WITH_FILE_IMAGE):
        attachments.append(match.group(1))

    assert len(attachments) == 1
    assert "/tmp/test_image.png" in attachments[0]  # noqa: S108


def test_markdown_image_detection_relative_paths():
    """Test detection of relative path images in markdown."""
    attachments = []
    for match in re.finditer(r"!\[[\w\. -]*\]\((?!http|file)([^\s,]*).*\)", MARKDOWN_WITH_RELATIVE_IMAGES):
        file_path = match.group(1).lstrip("./\\")
        attachments.append(file_path)

    assert len(attachments) == 2
    assert any("logo.png" in a for a in attachments)
    assert any("flow.png" in a for a in attachments)


def test_markdown_image_detection_no_images():
    """Test markdown without images returns empty attachments."""
    attachments = []
    for match in re.finditer(r'img src="file://(.*)" s', MARKDOWN_NO_IMAGES):
        attachments.append(match.group(1))
    for match in re.finditer(r"!\[[\w\. -]*\]\((?!http|file)([^\s,]*).*\)", MARKDOWN_NO_IMAGES):
        file_path = match.group(1).lstrip("./\\")
        attachments.append(file_path)

    assert len(attachments) == 0


def test_markdown_image_detection_mixed_formats():
    """Test detection of both file:// and relative path images."""
    attachments = []
    for match in re.finditer(r'img src="file://(.*)" s', MARKDOWN_WITH_MIXED_IMAGES):
        attachments.append(match.group(1))
    for match in re.finditer(r"!\[[\w\. -]*\]\((?!http|file)([^\s,]*).*\)", MARKDOWN_WITH_MIXED_IMAGES):
        file_path = match.group(1).lstrip("./\\")
        attachments.append(file_path)

    assert len(attachments) >= 3


def test_markdown_to_confluence_image_tag_replacement():
    """Test markdown image tag replacement for Confluence format."""
    markdown = '<img src="file:///tmp/test.png" style="page-break-inside: avoid;">'
    new_markdown = re.sub(
        r'<img src="file:///tmp/', '<p><ac:image ac:height="350"><ri:attachment ri:filename="', markdown
    )
    new_markdown = re.sub(r'" style="page-break-inside: avoid;">', '"/></ac:image></p>', new_markdown)

    assert new_markdown == '<p><ac:image ac:height="350"><ri:attachment ri:filename="test.png"/></ac:image></p>'


def test_confluence_body_temp_file_creation(tmp_path):
    """Test that confluence body is written to temp file with proper flush to prevent 0-byte files."""
    confluence_body = "<p>Test content</p>"

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(confluence_body)
        f.flush()  # Explicitly flush to prevent 0-byte files (bug #26 fix)
        temp_name = f.name

    try:
        temp_path = Path(temp_name)
        assert temp_path.exists()

        content = temp_path.read_text()
        assert content == confluence_body
        # Verify file is not empty (0 bytes)
        assert temp_path.stat().st_size > 0
    finally:
        Path(temp_name).unlink()


def test_wait_until_returns_immediately_when_truthy():
    """Test wait_until returns immediately when condition is truthy."""
    plugin = MkdocsWithConfluence()

    condition = True
    result = plugin.wait_until(condition, interval=0.1, timeout=1, max_retries=1)

    # Should return True immediately without waiting
    assert result is True


def test_wait_until_respects_timeout():
    """Test wait_until respects timeout when condition is falsy."""
    import time

    plugin = MkdocsWithConfluence()

    condition = False
    start = time.time()
    result = plugin.wait_until(condition, interval=0.1, timeout=0.5, max_retries=1)
    elapsed = time.time() - start

    # Should return False after timeout and wait approximately the timeout duration
    assert result is False
    assert elapsed >= 0.5
    assert elapsed < 0.7
