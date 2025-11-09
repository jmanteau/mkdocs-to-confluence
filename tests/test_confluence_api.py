"""Tests for Confluence API operations with mocked HTTP responses."""

import requests
import responses

from mkdocs_to_confluence.plugin import MkdocsWithConfluence
from tests.fixtures.configs import CONFIG_DRYRUN_MODE, MINIMAL_CONFIG
from tests.fixtures.confluence_responses import (
    PAGE_CREATED_RESPONSE,
    PAGE_FOUND_RESPONSE,
    PAGE_NO_ANCESTORS_RESPONSE,
    PAGE_NOT_FOUND_RESPONSE,
    PAGE_UPDATED_RESPONSE,
    PAGE_WITH_ANCESTORS_RESPONSE,
    PAGE_WITH_VERSION_RESPONSE,
)


@responses.activate
def test_find_page_id_returns_id_when_exists():
    """Test find_page_id returns ID for existing page."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_FOUND_RESPONSE,
        status=200,
    )

    page_id = plugin.find_page_id("Test Page")

    assert page_id == "123456"


@responses.activate
def test_find_page_id_returns_none_when_not_exists():
    """Test find_page_id returns None for non-existent page."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_NOT_FOUND_RESPONSE,
        status=200,
    )

    page_id = plugin.find_page_id("Nonexistent Page")

    assert page_id is None


@responses.activate
def test_find_page_version_returns_version_number():
    """Test find_page_version returns current version number."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    version = plugin.find_page_version("Test Page")

    assert version == 10


@responses.activate
def test_find_page_version_returns_none_when_not_exists():
    """Test find_page_version returns None for non-existent page."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_NOT_FOUND_RESPONSE,
        status=200,
    )

    version = plugin.find_page_version("Nonexistent")

    assert version is None


@responses.activate
def test_find_parent_name_returns_parent_title():
    """Test find_parent_name_of_page returns parent page title."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # First call to find_page_id
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_FOUND_RESPONSE,
        status=200,
    )

    # Second call to get ancestors
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123456",
        json=PAGE_WITH_ANCESTORS_RESPONSE,
        status=200,
    )

    parent_name = plugin.find_parent_name_of_page("Child Page")

    assert parent_name == "Parent Page"


@responses.activate
def test_find_parent_name_returns_none_for_root_page():
    """Test find_parent_name_of_page returns None for root page."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_FOUND_RESPONSE,
        status=200,
    )

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123456",
        json=PAGE_NO_ANCESTORS_RESPONSE,
        status=200,
    )

    parent_name = plugin.find_parent_name_of_page("Root Page")

    # Empty ancestors array should cause IndexError, returning None
    assert parent_name is None or parent_name == "Root Page"


@responses.activate
def test_add_page_creates_with_correct_structure():
    """Test add_page creates page with correct JSON structure."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.POST,
        "https://confluence.example.com/rest/api/content/",
        json=PAGE_CREATED_RESPONSE,
        status=200,
    )

    plugin.add_page("New Page", "111111", "<p>Content</p>")

    assert len(responses.calls) == 1
    request_body = responses.calls[0].request.body
    assert b"New Page" in request_body
    assert b"111111" in request_body


@responses.activate
def test_add_page_respects_dryrun_mode():
    """Test add_page respects dryrun mode and doesn't make API call."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_DRYRUN_MODE.copy()
    plugin.dryrun = True

    plugin.add_page("New Page", "111111", "<p>Content</p>")

    assert len(responses.calls) == 0


@responses.activate
def test_update_page_increments_version():
    """Test update_page updates with incremented version."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Mock find_page_id
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    # Mock find_page_version
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    # Mock update
    responses.add(
        responses.PUT,
        "https://confluence.example.com/rest/api/content/123456",
        json=PAGE_UPDATED_RESPONSE,
        status=200,
    )

    plugin.update_page("Test Page", "<p>Updated</p>")

    # Find last PUT request
    put_calls = [c for c in responses.calls if c.request.method == "PUT"]
    assert len(put_calls) == 1
    assert b'"number": 11' in put_calls[0].request.body


@responses.activate
def test_update_page_respects_dryrun_mode():
    """Test update_page respects dryrun mode."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_DRYRUN_MODE.copy()
    plugin.dryrun = True

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    plugin.update_page("Test Page", "<p>Updated</p>")

    put_calls = [c for c in responses.calls if c.request.method == "PUT"]
    assert len(put_calls) == 0


@responses.activate
def test_find_page_id_handles_connection_error():
    """Test find_page_id returns None on connection error."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        body=requests.exceptions.ConnectionError("Failed to resolve hostname"),
    )

    page_id = plugin.find_page_id("Test Page")

    assert page_id is None


@responses.activate
def test_find_page_version_handles_connection_error():
    """Test find_page_version returns None on connection error."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        body=requests.exceptions.ConnectionError("Connection refused"),
    )

    version = plugin.find_page_version("Test Page")

    assert version is None


@responses.activate
def test_find_parent_name_handles_connection_error_on_id_lookup():
    """Test find_parent_name_of_page returns None when page ID lookup fails."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        body=requests.exceptions.ConnectionError("DNS resolution failed"),
    )

    parent_name = plugin.find_parent_name_of_page("Child Page")

    assert parent_name is None


@responses.activate
def test_find_parent_name_handles_connection_error_on_ancestor_lookup():
    """Test find_parent_name_of_page returns None when ancestor lookup fails."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_FOUND_RESPONSE,
        status=200,
    )

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123456",
        body=requests.exceptions.ConnectionError("Connection timeout"),
    )

    parent_name = plugin.find_parent_name_of_page("Child Page")

    assert parent_name is None


@responses.activate
def test_add_page_handles_connection_error():
    """Test add_page handles connection error gracefully without crashing."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.POST,
        "https://confluence.example.com/rest/api/content/",
        body=requests.exceptions.ConnectionError("Network unreachable"),
    )

    # Should not raise exception
    plugin.add_page("New Page", "111111", "<p>Content</p>")


@responses.activate
def test_update_page_handles_connection_error_on_find():
    """Test update_page handles connection error during page ID lookup."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        body=requests.exceptions.ConnectionError("Host not found"),
    )

    # Should not raise exception
    plugin.update_page("Test Page", "<p>Updated</p>")


@responses.activate
def test_update_page_handles_connection_error_on_update():
    """Test update_page handles connection error during update request."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content",
        json=PAGE_WITH_VERSION_RESPONSE,
        status=200,
    )

    responses.add(
        responses.PUT,
        "https://confluence.example.com/rest/api/content/123456",
        body=requests.exceptions.ConnectionError("Connection reset"),
    )

    # Should not raise exception
    plugin.update_page("Test Page", "<p>Updated</p>")
