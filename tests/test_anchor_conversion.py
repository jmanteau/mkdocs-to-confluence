"""Tests for Confluence anchor conversion functionality."""

from __future__ import annotations

from src.mkdocs_to_confluence._vendor.md2cf.confluence_renderer import (
    convert_markdown_anchor_to_confluence,
)


def test_convert_markdown_anchor_basic():
    """Convert simple markdown anchor to Confluence format."""
    page_title = "Test Page"
    markdown_anchor = "simple-heading"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "TestPage-SimpleHeading"


def test_convert_markdown_anchor_with_spaces_in_title():
    """Convert anchor when page title contains spaces."""
    page_title = "My Test Page Title"
    markdown_anchor = "section-name"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "MyTestPageTitle-SectionName"


def test_convert_markdown_anchor_complex_title():
    """Convert anchor for the real-world example from issue."""
    page_title = "Foundations for Internet Publishing Serverless Apps Blueprint"
    markdown_anchor = "architecture-overview"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "FoundationsforInternetPublishingServerlessAppsBlueprint-ArchitectureOverview"


def test_convert_markdown_anchor_with_multiple_words():
    """Convert multi-word markdown anchor to PascalCase."""
    page_title = "Documentation"
    markdown_anchor = "getting-started-with-installation"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "Documentation-GettingStartedWithInstallation"


def test_convert_markdown_anchor_empty_fragment():
    """Handle empty anchor fragment."""
    page_title = "Test Page"
    markdown_anchor = ""

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "TestPage"


def test_convert_markdown_anchor_single_word():
    """Convert single-word anchor."""
    page_title = "Guide"
    markdown_anchor = "introduction"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "Guide-Introduction"


def test_convert_markdown_anchor_with_numbers():
    """Convert anchor containing numbers."""
    page_title = "API Documentation"
    markdown_anchor = "version-2-0-changes"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "APIDocumentation-Version20Changes"


def test_convert_markdown_anchor_special_chars_in_title():
    """Handle special characters in page title."""
    page_title = "Test & Development (Guide)"
    markdown_anchor = "quick-start"

    result = convert_markdown_anchor_to_confluence(markdown_anchor, page_title)

    assert result == "Test&Development(Guide)-QuickStart"
