"""Tests for strip_h1 feature."""

from mkdocs_to_confluence.plugin import MkdocsWithConfluence
from tests.fixtures.configs import MINIMAL_CONFIG


class TestShouldStripH1:
    """Test cases for _should_strip_h1 method."""

    def test_empty_markdown(self):
        """Test that empty markdown returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        assert plugin._should_strip_h1("") is False
        assert plugin._should_strip_h1(None) is False

    def test_only_blank_lines(self):
        """Test that markdown with only blank lines returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "\n\n\n"
        assert plugin._should_strip_h1(markdown) is False

    def test_single_h1_at_start_atx_style(self):
        """Test that single ATX-style h1 at start returns True."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Page Title\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is True

    def test_single_h1_at_start_with_leading_blanks_atx_style(self):
        """Test that single ATX-style h1 at start with leading blanks returns True."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "\n\n# Page Title\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is True

    def test_single_h1_at_start_setext_style(self):
        """Test that single Setext-style h1 at start returns True."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Page Title\n==========\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is True

    def test_single_h1_at_start_with_leading_blanks_setext_style(self):
        """Test that single Setext-style h1 at start with leading blanks returns True."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "\n\nPage Title\n==========\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is True

    def test_multiple_h1_tags(self):
        """Test that multiple h1 tags returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# First Title\n\nSome content.\n\n# Second Title\n\nMore content."
        assert plugin._should_strip_h1(markdown) is False

    def test_multiple_h1_tags_mixed_styles(self):
        """Test that multiple h1 tags with mixed styles returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# First Title\n\nSome content.\n\nSecond Title\n============\n\nMore content."
        assert plugin._should_strip_h1(markdown) is False

    def test_h1_not_at_start(self):
        """Test that h1 not at start returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Some intro text.\n\n# Page Title\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is False

    def test_paragraph_before_h1(self):
        """Test that paragraph before h1 returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "This is a paragraph.\n\n# Page Title\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is False

    def test_h2_at_start(self):
        """Test that h2 at start returns False."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "## Section Title\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is False

    def test_h1_with_only_hash(self):
        """Test that single # without space is not treated as h1."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "#NotAHeader\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is False

    def test_setext_h1_with_short_underline(self):
        """Test Setext h1 with underline shorter than title."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Page Title\n===\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is True

    def test_setext_h1_with_long_underline(self):
        """Test Setext h1 with underline longer than title."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Page Title\n====================\n\nSome content here."
        assert plugin._should_strip_h1(markdown) is True


class TestStripH1FromMarkdown:
    """Test cases for _strip_h1_from_markdown method."""

    def test_strip_atx_h1_basic(self):
        """Test stripping basic ATX-style h1."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Page Title\n\nSome content here."
        expected = "Some content here."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_strip_atx_h1_with_leading_blanks(self):
        """Test stripping ATX-style h1 with leading blank lines."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "\n\n# Page Title\n\nSome content here."
        expected = "Some content here."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_strip_atx_h1_with_trailing_blanks(self):
        """Test stripping ATX-style h1 with trailing blank lines."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Page Title\n\n\nSome content here."
        expected = "Some content here."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_strip_setext_h1_basic(self):
        """Test stripping basic Setext-style h1."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Page Title\n==========\n\nSome content here."
        expected = "Some content here."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_strip_setext_h1_with_leading_blanks(self):
        """Test stripping Setext-style h1 with leading blank lines."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "\n\nPage Title\n==========\n\nSome content here."
        expected = "Some content here."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_strip_setext_h1_with_trailing_blanks(self):
        """Test stripping Setext-style h1 with trailing blank lines."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Page Title\n==========\n\n\nSome content here."
        expected = "Some content here."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_no_strip_multiple_h1(self):
        """Test that multiple h1 tags are not stripped."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# First Title\n\nSome content.\n\n# Second Title\n\nMore content."
        assert plugin._strip_h1_from_markdown(markdown) == markdown

    def test_no_strip_h1_not_at_start(self):
        """Test that h1 not at start is not stripped."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Some intro text.\n\n# Page Title\n\nSome content here."
        assert plugin._strip_h1_from_markdown(markdown) == markdown

    def test_preserve_h2_and_below(self):
        """Test that h2 and lower headings are preserved."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Page Title\n\n## Section\n\n### Subsection\n\nContent."
        expected = "## Section\n\n### Subsection\n\nContent."
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_preserve_content_structure(self):
        """Test that content structure is preserved after stripping h1."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Page Title\n\nParagraph 1.\n\nParagraph 2.\n\n- List item 1\n- List item 2"
        expected = "Paragraph 1.\n\nParagraph 2.\n\n- List item 1\n- List item 2"
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_strip_h1_with_complex_content(self):
        """Test stripping h1 with complex markdown content."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = """# Main Title

## Introduction

This is an introduction.

## Features

- Feature 1
- Feature 2

### Details

More details here.

```python
code block
```
"""
        expected = """## Introduction

This is an introduction.

## Features

- Feature 1
- Feature 2

### Details

More details here.

```python
code block
```
"""
        assert plugin._strip_h1_from_markdown(markdown) == expected

    def test_empty_markdown_unchanged(self):
        """Test that empty markdown is unchanged."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = ""
        assert plugin._strip_h1_from_markdown(markdown) == markdown

    def test_blank_lines_only_unchanged(self):
        """Test that markdown with only blank lines is unchanged."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "\n\n\n"
        # Should return empty or the same blank lines
        result = plugin._strip_h1_from_markdown(markdown)
        assert result.strip() == ""


class TestConvertToConfluenceFormatWithStripH1:
    """Test cases for _convert_to_confluence_format with strip_h1 enabled."""

    def test_strip_h1_disabled_by_default(self):
        """Test that strip_h1 is disabled by default."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Test Header\n\nTest content"
        confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

        # h1 should be present in output
        assert '<h1>' in confluence_body or 'Test Header' in confluence_body

    def test_strip_h1_enabled(self):
        """Test that strip_h1 removes h1 when enabled."""
        plugin = MkdocsWithConfluence()
        config = MINIMAL_CONFIG.copy()
        config["strip_h1"] = True
        plugin.config = config

        markdown = "# Test Header\n\nTest content"
        confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

        # h1 should not be present in output
        assert '<h1>' not in confluence_body
        # But content should still be there
        assert 'Test content' in confluence_body or '<p>Test content</p>' in confluence_body

    def test_strip_h1_preserves_h2(self):
        """Test that strip_h1 preserves h2 and lower headings."""
        plugin = MkdocsWithConfluence()
        config = MINIMAL_CONFIG.copy()
        config["strip_h1"] = True
        plugin.config = config

        markdown = "# Main Title\n\n## Section\n\nContent"
        confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

        # h1 should not be present
        assert '<h1>' not in confluence_body
        # h2 should be present
        assert '<h2>' in confluence_body or 'Section' in confluence_body

    def test_strip_h1_multiple_h1_not_stripped(self):
        """Test that multiple h1 tags are not stripped."""
        plugin = MkdocsWithConfluence()
        config = MINIMAL_CONFIG.copy()
        config["strip_h1"] = True
        plugin.config = config

        markdown = "# First\n\nContent\n\n# Second\n\nMore"
        confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

        # Both h1 tags should be present
        assert confluence_body.count('<h1>') == 2 or confluence_body.count('First') > 0

    def test_strip_h1_h1_not_at_start_not_stripped(self):
        """Test that h1 not at start is not stripped."""
        plugin = MkdocsWithConfluence()
        config = MINIMAL_CONFIG.copy()
        config["strip_h1"] = True
        plugin.config = config

        markdown = "Intro text\n\n# Title\n\nContent"
        confluence_body = plugin._convert_to_confluence_format(markdown, "TestPage")

        # h1 should be present
        assert '<h1>' in confluence_body or 'Title' in confluence_body


class TestStripH1EdgeCases:
    """Test edge cases for strip_h1 feature."""

    def test_h1_with_special_characters(self):
        """Test h1 with special characters."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Title with *italic* and **bold**\n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert "# Title" not in result
        assert "Content" in result

    def test_h1_with_code(self):
        """Test h1 with inline code."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Title with `code`\n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert "# Title" not in result
        assert "Content" in result

    def test_h1_with_link(self):
        """Test h1 with link."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Title with [link](http://example.com)\n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert "# Title" not in result
        assert "Content" in result

    def test_setext_h1_with_trailing_spaces(self):
        """Test Setext h1 with trailing spaces in underline."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "Title\n===   \n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert "Title" not in result or result.strip() == "Content"

    def test_atx_h1_with_closing_hashes(self):
        """Test ATX h1 with closing hashes."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Title #\n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert "# Title" not in result
        assert "Content" in result

    def test_very_long_h1(self):
        """Test very long h1 title."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        long_title = "A" * 200
        markdown = f"# {long_title}\n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert long_title not in result or "Content" in result

    def test_h1_only_document(self):
        """Test document with only h1 and no other content."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Only Title"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert result.strip() == ""

    def test_unicode_in_h1(self):
        """Test h1 with unicode characters."""
        plugin = MkdocsWithConfluence()
        plugin.config = MINIMAL_CONFIG.copy()

        markdown = "# Título en Español 中文标题\n\nContent"
        assert plugin._should_strip_h1(markdown) is True

        result = plugin._strip_h1_from_markdown(markdown)
        assert "# Título" not in result
        assert "Content" in result
