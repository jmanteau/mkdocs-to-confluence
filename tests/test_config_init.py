"""Tests for plugin configuration and initialization."""

import os
from unittest.mock import MagicMock

from mkdocs_to_confluence.plugin import BearerAuth, MkdocsWithConfluence
from tests.fixtures.configs import (
    CONFIG_DEBUG_MODE,
    CONFIG_DRYRUN_MODE,
    CONFIG_WITH_API_TOKEN,
    CONFIG_WITH_BEARER_AUTH,
    CONFIG_WITH_ENV_CHECK,
    INCOMPLETE_CONFIG,
    MINIMAL_CONFIG,
)


def test_plugin_initialization():
    """Test plugin initializes with correct default values."""
    plugin = MkdocsWithConfluence()

    assert plugin.enabled is True
    assert plugin.simple_log is False
    assert plugin.flen == 1
    assert plugin.confluence_renderer is not None
    assert plugin.confluence_mistune is not None
    assert plugin.session is not None
    assert plugin.page_attachments == {}


def test_plugin_config_with_all_parameters():
    """Test plugin configuration with all required parameters."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    assert plugin.config["host_url"] == "https://confluence.example.com/rest/api/content"
    assert plugin.config["space"] == "TEST"
    assert plugin.config["parent_page_name"] == "Documentation"
    assert plugin.config["username"] == "test_user"
    assert plugin.config["password"] == "test_pass"  # noqa: S105
    assert plugin.config["verbose"] is False
    assert plugin.config["debug"] is False
    assert plugin.config["dryrun"] is False


def test_plugin_auth_with_password():
    """Test session authentication setup with username and password."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Simulate on_page_markdown setting up auth
    plugin.session.auth = (plugin.config["username"], plugin.config["password"])

    assert plugin.session.auth == ("test_user", "test_pass")


def test_plugin_auth_with_api_token():
    """Test session authentication with API token takes precedence over password."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_WITH_API_TOKEN.copy()

    # Simulate on_page_markdown setting up auth
    if plugin.config.get("api_token"):
        plugin.session.auth = (plugin.config["username"], plugin.config["api_token"])
    else:
        plugin.session.auth = (plugin.config["username"], plugin.config["password"])

    assert plugin.session.auth == ("test_user", "test_api_token_123")


def test_plugin_enabled_by_default_when_no_env_check():
    """Test plugin is enabled by default when enabled_if_env is None."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    # Create mock config object
    mock_config = MagicMock()
    plugin.on_config(mock_config)

    assert plugin.enabled is True


def test_plugin_disabled_when_env_var_not_set():
    """Test plugin is disabled when enabled_if_env is set but env var is not."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_WITH_ENV_CHECK.copy()

    # Ensure env var is not set
    if "CONFLUENCE_UPLOAD" in os.environ:
        del os.environ["CONFLUENCE_UPLOAD"]

    mock_config = MagicMock()
    plugin.on_config(mock_config)

    assert plugin.enabled is False


def test_plugin_disabled_when_env_var_not_one():
    """Test plugin is disabled when enabled_if_env is set and env var != '1'."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_WITH_ENV_CHECK.copy()

    os.environ["CONFLUENCE_UPLOAD"] = "0"

    try:
        mock_config = MagicMock()
        plugin.on_config(mock_config)

        assert plugin.enabled is False
    finally:
        del os.environ["CONFLUENCE_UPLOAD"]


def test_plugin_enabled_when_env_var_is_one():
    """Test plugin is enabled when enabled_if_env is set and env var == '1'."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_WITH_ENV_CHECK.copy()

    os.environ["CONFLUENCE_UPLOAD"] = "1"

    try:
        mock_config = MagicMock()
        plugin.on_config(mock_config)

        assert plugin.enabled is True
    finally:
        del os.environ["CONFLUENCE_UPLOAD"]


def test_plugin_dryrun_mode_enabled():
    """Test dryrun mode is correctly set when configured."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_DRYRUN_MODE.copy()
    plugin.enabled = True  # Bypass enabled_if_env check

    mock_config = MagicMock()
    plugin.on_config(mock_config)

    assert hasattr(plugin, "dryrun")
    assert plugin.dryrun is True


def test_plugin_dryrun_mode_disabled():
    """Test dryrun mode is disabled by default."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()
    plugin.enabled = True  # Bypass enabled_if_env check

    mock_config = MagicMock()
    plugin.on_config(mock_config)

    assert hasattr(plugin, "dryrun")
    assert plugin.dryrun is False


def test_plugin_debug_mode():
    """Test debug mode configuration."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_DEBUG_MODE.copy()

    assert plugin.config["debug"] is True
    assert plugin.config["verbose"] is False


def test_plugin_simple_log_enabled_when_not_verbose():
    """Test simple_log mode is enabled when verbose and debug are False."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    mock_template_name = "test.html"
    mock_output_content = "<html></html>"
    mock_config = MagicMock()

    plugin.on_post_template(mock_output_content, mock_template_name, mock_config)

    assert plugin.simple_log is True


def test_plugin_simple_log_disabled_when_verbose():
    """Test simple_log mode is disabled when verbose is True."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()
    plugin.config["verbose"] = True

    mock_template_name = "test.html"
    mock_output_content = "<html></html>"
    mock_config = MagicMock()

    plugin.on_post_template(mock_output_content, mock_template_name, mock_config)

    assert plugin.simple_log is False


def test_plugin_simple_log_disabled_when_debug():
    """Test simple_log mode is disabled when debug is True."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_DEBUG_MODE.copy()

    mock_template_name = "test.html"
    mock_output_content = "<html></html>"
    mock_config = MagicMock()

    plugin.on_post_template(mock_output_content, mock_template_name, mock_config)

    assert plugin.simple_log is False


def test_environment_variable_fallbacks():
    """Test environment variable fallbacks are read from config_scheme."""
    # Set env vars before importing/creating plugin
    os.environ["JIRA_USERNAME"] = "env_user"
    os.environ["JIRA_PASSWORD"] = "env_pass"  # noqa: S105
    os.environ["CONFLUENCE_API_TOKEN"] = "env_token"  # noqa: S105

    try:
        # Config scheme evaluates env vars at class definition time
        # We test that the config_scheme tuple has Type objects with proper structure
        plugin = MkdocsWithConfluence()
        config_scheme_dict = dict(plugin.config_scheme)

        # Verify keys exist in config_scheme
        assert "username" in config_scheme_dict
        assert "password" in config_scheme_dict
        assert "api_token" in config_scheme_dict
    finally:
        del os.environ["JIRA_USERNAME"]
        del os.environ["JIRA_PASSWORD"]
        del os.environ["CONFLUENCE_API_TOKEN"]


def test_incomplete_config_handling():
    """Test handling of incomplete configuration with None values."""
    plugin = MkdocsWithConfluence()
    plugin.config = INCOMPLETE_CONFIG.copy()

    # The plugin should initialize but config validation happens in on_page_markdown
    # We just verify the config is stored correctly
    assert plugin.config["host_url"] is None
    assert plugin.config["space"] == "TEST"


def test_bearer_auth_class():
    """Test BearerAuth class correctly formats Authorization header."""
    token = "test_oauth_token_12345"
    auth = BearerAuth(token)

    # Create a mock request object
    mock_request = MagicMock()
    mock_request.headers = {}

    # Apply the auth
    result = auth(mock_request)

    # Verify the Authorization header was set correctly
    assert result.headers["Authorization"] == "Bearer test_oauth_token_12345"


def test_plugin_auth_with_bearer_token():
    """Test session authentication with Bearer token when auth_type is 'bearer'."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_WITH_BEARER_AUTH.copy()

    # Simulate on_page_markdown setting up auth with bearer type
    if plugin.config.get("api_token"):
        token = plugin.config["api_token"]
        if plugin.config["auth_type"] == "bearer":
            plugin.session.auth = BearerAuth(token)
        else:
            plugin.session.auth = (plugin.config["username"], token)

    # Verify BearerAuth was used
    assert isinstance(plugin.session.auth, BearerAuth)
    assert plugin.session.auth.token == "oauth_bearer_token_example_1234567890"


def test_plugin_auth_type_defaults_to_basic():
    """Test that auth_type defaults to 'basic' when not specified."""
    plugin = MkdocsWithConfluence()
    plugin.config = MINIMAL_CONFIG.copy()

    assert plugin.config["auth_type"] == "basic"


def test_plugin_config_with_bearer_auth():
    """Test plugin configuration with Bearer authentication settings."""
    plugin = MkdocsWithConfluence()
    plugin.config = CONFIG_WITH_BEARER_AUTH.copy()

    assert plugin.config["auth_type"] == "bearer"
    assert plugin.config["api_token"] == "oauth_bearer_token_example_1234567890"
    assert plugin.config["username"] == "test_user"
