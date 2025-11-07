"""Minimal tests for mkdocs-with-confluence plugin."""

import sys

from mkdocs_to_confluence.plugin import DummyFile, MkdocsWithConfluence, nostdout


def test_plugin_initialization():
    """Test that the plugin can be initialized."""
    plugin = MkdocsWithConfluence()
    assert plugin.enabled is True
    assert plugin.simple_log is False
    assert plugin.flen == 1


def test_dummy_file():
    """Test DummyFile helper class."""
    dummy = DummyFile()
    # Should not raise any errors
    dummy.write("test")
    dummy.write("")


def test_nostdout():
    """Test nostdout context manager."""
    original_stdout = sys.stdout
    with nostdout():
        # stdout should be redirected
        assert sys.stdout != original_stdout
        sys.stdout.write("This should not appear")

    # stdout should be restored
    assert sys.stdout == original_stdout


def test_get_file_sha1(tmp_path):
    """Test file SHA1 calculation."""
    plugin = MkdocsWithConfluence()

    # Create a temporary file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    sha1 = plugin.get_file_sha1(str(test_file))
    assert sha1 is not None
    assert len(sha1) == 40  # SHA1 hash is 40 characters
