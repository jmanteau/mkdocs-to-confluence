"""Test configuration fixtures."""

# Minimal valid plugin configuration
MINIMAL_CONFIG = {
    "host_url": "https://confluence.example.com/rest/api/content",
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "password": "test_pass",
    "auth_type": "basic",
    "enabled_if_env": None,
    "verbose": False,
    "debug": False,
    "dryrun": False,
    "export_dir": "confluence-export",
    "strip_h1": False,
}

# Configuration with API token
CONFIG_WITH_API_TOKEN = {
    "host_url": "https://confluence.example.com/rest/api/content",
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "api_token": "test_api_token_123",
    "password": "test_pass",
    "auth_type": "basic",
    "enabled_if_env": None,
    "verbose": False,
    "debug": False,
    "dryrun": False,
    "export_dir": "confluence-export",
}

# Configuration with Bearer token authentication
CONFIG_WITH_BEARER_AUTH = {
    "host_url": "https://confluence.example.com/rest/api/content",
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "api_token": "oauth_bearer_token_example_1234567890",
    "password": None,
    "auth_type": "bearer",
    "enabled_if_env": None,
    "verbose": False,
    "debug": False,
    "dryrun": False,
    "export_dir": "confluence-export",
}

# Configuration with debug enabled
CONFIG_DEBUG_MODE = {
    "host_url": "https://confluence.example.com/rest/api/content",
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "password": "test_pass",
    "auth_type": "basic",
    "enabled_if_env": None,
    "verbose": False,
    "debug": True,
    "dryrun": False,
    "export_dir": "confluence-export",
}

# Configuration with dryrun enabled
CONFIG_DRYRUN_MODE = {
    "host_url": "https://confluence.example.com/rest/api/content",
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "password": "test_pass",
    "auth_type": "basic",
    "enabled_if_env": None,
    "verbose": False,
    "debug": False,
    "dryrun": True,
    "export_dir": "confluence-export",
}

# Configuration with enabled_if_env
CONFIG_WITH_ENV_CHECK = {
    "host_url": "https://confluence.example.com/rest/api/content",
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "password": "test_pass",
    "auth_type": "basic",
    "enabled_if_env": "CONFLUENCE_UPLOAD",
    "verbose": False,
    "debug": False,
    "dryrun": False,
    "export_dir": "confluence-export",
}

# Incomplete configuration (missing required fields)
INCOMPLETE_CONFIG = {
    "host_url": None,
    "space": "TEST",
    "parent_page_name": "Documentation",
    "username": "test_user",
    "password": "test_pass",
    "auth_type": "basic",
    "enabled_if_env": None,
    "verbose": False,
    "debug": False,
    "dryrun": False,
    "export_dir": "confluence-export",
}
