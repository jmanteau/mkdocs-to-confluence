"""MkDocs plugin for publishing to Confluence."""

from __future__ import annotations

import contextlib
import hashlib
import logging
import mimetypes
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable
from importlib.metadata import version
from os import environ
from pathlib import Path
from time import sleep
from typing import Any

import mistune
import requests
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from requests.auth import AuthBase

from mkdocs_to_confluence._vendor.md2cf.confluence_renderer import ConfluenceRenderer
from mkdocs_to_confluence.exporter import ConfluenceExporter

TEMPLATE_BODY = "<p> TEMPLATE </p>"

logger = logging.getLogger("mkdocs.plugins.mkdocs-with-confluence")


class BearerAuth(AuthBase):
    """Attaches OAuth Bearer Token Authentication to the given Request object."""

    def __init__(self, token):
        """Store the OAuth bearer token used for authentication.

        Args:
            token (str): OAuth access token issued by Atlassian.

        """
        self.token = token

    def __call__(self, r):
        """Attach the bearer token to an outgoing request.

        Args:
            r (requests.PreparedRequest): The request object to mutate in place.

        Returns:
            requests.PreparedRequest: The same request instance, with the
            Authorization header populated.

        """
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


@contextlib.contextmanager
def nostdout():
    """Temporarily silence ``sys.stdout`` within the managed context."""
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout


class DummyFile:
    """File-like object that discards all writes."""

    def write(self, x):
        """Discard written content."""
        pass


class MkdocsWithConfluence(BasePlugin):
    """MkDocs plugin to publish documentation to Confluence."""

    _id = 0
    config_scheme = (
        ("host_url", config_options.Type(str, default=None)),
        ("space", config_options.Type(str, default=None)),
        ("parent_page_name", config_options.Type(str, default=None)),
        ("username", config_options.Type(str, default=environ.get("JIRA_USERNAME", None))),
        # If api_token is specified, password is ignored
        ("api_token", config_options.Type(str, default=environ.get("CONFLUENCE_API_TOKEN", None))),
        ("password", config_options.Type(str, default=environ.get("JIRA_PASSWORD", None))),
        # Authentication type: 'basic' (default) or 'bearer' for OAuth tokens
        ("auth_type", config_options.Choice(["basic", "bearer"], default="basic")),
        ("enabled_if_env", config_options.Type(str, default=None)),
        ("verbose", config_options.Type(bool, default=False)),
        ("debug", config_options.Type(bool, default=False)),
        ("debug_diff", config_options.Type(bool, default=False)),
        ("dryrun", config_options.Type(bool, default=False)),
        ("export_dir", config_options.Type(str, default="confluence-export")),
        ("strip_h1", config_options.Type(bool, default=False)),
        ("cleanup_orphaned_pages", config_options.Type(bool, default=False)),
        ("keep_pages", config_options.Type(list, default=[])),
        ("page_label", config_options.Type(str, default="auto-generated-docs")),
    )

    def __init__(self):
        """Initialize plugin with default settings."""
        self.enabled = True
        self.confluence_renderer = ConfluenceRenderer()
        self.confluence_mistune = mistune.Markdown(renderer=self.confluence_renderer)
        self.simple_log = False
        self.flen = 1
        self.session = requests.Session()
        self.page_attachments = {}
        self.dryrun = False
        self.exporter = None
        self.synced_pages: set[str] = set()

    def _safe_request(self, method, url, context, **kwargs):
        """Execute HTTP request with connection error handling.

        Wraps requests to catch connection errors and log them properly
        instead of crashing the build process.

        Args:
            method: HTTP method ('get', 'post', 'put')
            url: Request URL
            context: Description of operation for error messages
            **kwargs: Additional arguments passed to requests method

        Returns:
            Response object if successful, None if connection error occurred

        """
        try:
            response = getattr(self.session, method)(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            if "Failed to resolve" in error_msg or "nodename nor servname" in error_msg:
                host = self.config.get('host_url', 'unknown')
                logger.error(
                    f"Cannot connect to Confluence: DNS resolution failed for '{host}'. "
                    f"Context: {context}"
                )
            elif "Connection refused" in error_msg:
                host = self.config.get('host_url', 'unknown')
                logger.error(
                    f"Cannot connect to Confluence: Connection refused to '{host}'. "
                    f"Context: {context}"
                )
            else:
                logger.error(
                    f"Cannot connect to Confluence: Network error. "
                    f"Context: {context}. Error: {error_msg}"
                )
            return None
        except requests.exceptions.Timeout as e:
            logger.error(
                f"Confluence request timed out. "
                f"Context: {context}. Error: {e}"
            )
            return None
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Confluence request failed. "
                f"Context: {context}. Error: {e}"
            )
            return None

    def on_nav(self, nav, config, files):
        """Build navigation structure from MkDocs nav.

        Args:
            nav (mkdocs.structure.nav.Navigation): Navigation object produced by MkDocs.
            config (mkdocs.config.base.Config): Active MkDocs configuration.
            files (mkdocs.structure.files.Files): Collection of files included in the build.

        """
        MkdocsWithConfluence.tab_nav = []
        navigation_items = nav.__repr__()

        for n in navigation_items.split("\n"):
            leading_spaces = len(n) - len(n.lstrip(" "))
            spaces = leading_spaces * " "
            if "Page" in n:
                try:
                    self.page_title = self.__get_page_title(n)
                    if self.page_title is None:
                        raise AttributeError
                except AttributeError:
                    self.page_local_path = self.__get_page_url(n)
                    logger.warning(
                        f"Page from path {self.page_local_path} has no "
                        f"entity in the mkdocs.yml nav section. It will be uploaded "
                        f"to Confluence, but you may not see it on the web server!"
                    )
                    self.page_local_name = self.__get_page_name(n)
                    self.page_title = self.page_local_name

                p = spaces + self.page_title
                MkdocsWithConfluence.tab_nav.append(p)
            if "Section" in n:
                try:
                    self.section_title = self.__get_section_title(n)
                    if self.section_title is None:
                        raise AttributeError
                except AttributeError:
                    self.section_local_path = self.__get_page_url(n)
                    logger.warning(
                        f"Section from path {self.section_local_path} has no "
                        f"entity in the mkdocs.yml nav section. It will be uploaded "
                        f"to Confluence, but you may not see it on the web server!"
                    )
                    self.section_local_name = self.__get_section_title(n)
                    self.section_title = self.section_local_name
                s = spaces + self.section_title
                MkdocsWithConfluence.tab_nav.append(s)

    def on_files(self, files, config):
        """Count documentation pages.

        Args:
            files (mkdocs.structure.files.Files): Files selected for the build.
            config (mkdocs.config.base.Config): Active MkDocs configuration.

        """
        pages = files.documentation_pages()
        self.flen = len(pages)
        logger.info(f"Number of files in directory tree: {self.flen}")
        if self.flen == 0:
            logger.error("No documentation pages in directory tree, please add at least one!")

    def on_post_template(self, output_content, template_name, config):
        """Configure logging mode based on verbosity settings.

        Args:
            output_content (str): Rendered output from MkDocs.
            template_name (str): Name of the template used for rendering.
            config (mkdocs.config.base.Config): Active MkDocs configuration.

        """
        if self.config["verbose"] is False and self.config["debug"] is False:
            self.simple_log = True
            logger.info("Mkdocs With Confluence: Start exporting markdown pages... (simple logging)")
        else:
            self.simple_log = False

    def on_config(self, config):
        """Configure plugin based on environment and settings.

        Args:
            config (mkdocs.config.base.Config): Active MkDocs configuration being initialized.

        """
        # Print version
        try:
            plugin_version = version("mkdocs-to-confluence")
            logger.info(f"Mkdocs With Confluence v{plugin_version}")
        except Exception:
            logger.info("Mkdocs With Confluence (version unknown)")

        # Always set dryrun regardless of enabled status
        if self.config["dryrun"]:
            logger.warning("Mkdocs With Confluence - DRYRUN MODE turned ON")
            self.dryrun = True
            # Initialize exporter for dry-run mode
            export_dir = Path(self.config["export_dir"])
            self.exporter = ConfluenceExporter(export_dir)
            logger.info(f"Mkdocs With Confluence: Exporting to {export_dir}")
        else:
            self.dryrun = False
            self.exporter = None

        # Handle conditional enabling based on environment variable
        env_name = self.config.get("enabled_if_env")
        if env_name is not None:
            # Conditional execution based on environment variable
            self.enabled = os.environ.get(env_name) == "1"
            if not self.enabled:
                logger.warning(
                    "Mkdocs With Confluence: Exporting MKDOCS pages to Confluence turned OFF: "
                    f"(set environment variable {env_name} to 1 to enable)"
                )
                return
            logger.info(
                "Mkdocs With Confluence: Exporting MKDOCS pages to Confluence "
                f"turned ON by var {env_name}==1!"
            )
        else:
            # No conditional - enabled by default
            logger.info("Mkdocs With Confluence: Exporting MKDOCS pages to Confluence turned ON by default!")
            self.enabled = True

    def _resolve_page_parents(self, page):
        """Resolve parent page hierarchy for a given page.

        Args:
            page (mkdocs.structure.pages.Page): Page whose parent chain should
                be reconstructed from the navigation tree.

        Returns:
            list: A list of parent page titles from root (main_parent) to direct parent.
                  The last element is the direct parent of the page.
                  Example: ["Home", "Getting Started", "Installation"]

        """
        # Determine main parent (root)
        if self.config["parent_page_name"] is not None:
            main_parent = self.config["parent_page_name"]
        else:
            main_parent = self.config["space"]

        # Build parent chain from ancestors (reverse order since ancestors go from direct parent upwards)
        parent_chain = []

        if self.config["debug"]:
            logger.debug(f"Resolving parent chain for page, found {len(page.ancestors)} ancestors")

        # Process all ancestors to build the full hierarchy
        for i in range(len(page.ancestors) - 1, -1, -1):
            try:
                parent_title = self.__get_section_title(page.ancestors[i].__repr__())
                if parent_title:
                    parent_chain.append(parent_title)
                    if self.config["debug"]:
                        logger.debug(f"Added ancestor level {i}: {parent_title}")
            except Exception as e:
                if self.config["debug"]:
                    logger.debug(f"Error processing ancestor at index {i}: {e}")

        # If no parents found, use main_parent as the direct parent
        if not parent_chain:
            if self.config["debug"]:
                logger.debug(
                    f"No ancestors found. Using main parent {main_parent} as direct parent"
                )
            parent_chain = [main_parent]
        else:
            # Ensure main_parent is at the root if not already present
            if parent_chain[0] != main_parent:
                parent_chain.insert(0, main_parent)

        if self.config["debug"]:
            logger.debug(f"Final parent chain: {parent_chain}")

        return parent_chain

    def _extract_attachments(self, markdown):
        """Extract attachment paths referenced within markdown.

        Args:
            markdown (str): Markdown source of the page currently processed.

        Returns:
            list: Relative file paths discovered in image references.

        """
        attachments = []
        try:
            # Find images with file:// protocol
            for match in re.finditer(r'img src="file://(.*)" s', markdown):
                if self.config["debug"]:
                    logger.debug(f"FOUND IMAGE: {match.group(1)}")
                attachments.append(match.group(1))

            # Find images in markdown format ![](path)
            for match in re.finditer(r"!\[[\w\. -]*\]\((?!http|file)([^\s,]*).*\)", markdown):
                file_path = match.group(1).lstrip("./\\")
                attachments.append(file_path)

                if self.config["debug"]:
                    logger.debug(f"FOUND IMAGE: {file_path}")
                attachments.append("docs/" + file_path.replace("../", ""))

        except AttributeError as e:
            if self.config["debug"]:
                logger.debug(f"WARN(({e}): No images found in markdown. Proceed..")

        return attachments

    def _should_strip_h1(self, markdown):
        """Determine if the h1 should be stripped from the markdown content.

        The h1 will be stripped only if ALL of the following conditions are met:
        1. The h1 is the very first content element (ignoring blank lines)
        2. There is exactly one h1 in the entire document

        Args:
            markdown (str): Markdown content to inspect.

        Returns:
            bool: True if h1 should be stripped, False otherwise

        """
        if not markdown:
            return False

        # Remove leading blank lines to find first content
        lines = markdown.split('\n')
        first_content_idx = None
        for idx, line in enumerate(lines):
            if line.strip():
                first_content_idx = idx
                break

        if first_content_idx is None:
            # Empty document
            return False

        first_line = lines[first_content_idx].strip()

        # Check if first content is an h1 (both # and === syntax)
        is_first_h1 = False
        if first_line.startswith('# '):
            # ATX-style h1: # Title
            is_first_h1 = True
        elif first_content_idx + 1 < len(lines):
            # Check for Setext-style h1: Title followed by ===
            next_line = lines[first_content_idx + 1].strip()
            if next_line and all(c == '=' for c in next_line):
                is_first_h1 = True

        if not is_first_h1:
            return False

        # Count total h1 occurrences in the document
        h1_count = 0

        # Count ATX-style h1s: # Title
        h1_count += len(re.findall(r'^# [^#]', markdown, re.MULTILINE))

        # Count Setext-style h1s: Title\n===
        # Look for lines followed by a line of only = characters
        setext_pattern = r'^.+\n=+\s*$'
        h1_count += len(re.findall(setext_pattern, markdown, re.MULTILINE))

        # Only strip if there's exactly one h1
        return h1_count == 1

    def _strip_h1_from_markdown(self, markdown):
        """Remove the first h1 from markdown content if conditions are met.

        Args:
            markdown (str): Markdown content to transform.

        Returns:
            str: Markdown with h1 removed if applicable, otherwise unchanged

        """
        if not self._should_strip_h1(markdown):
            return markdown

        lines = markdown.split('\n')
        result_lines = []
        h1_removed = False
        h1_title = None

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip leading blank lines
            if not h1_removed and not line.strip():
                i += 1
                continue

            # Check for ATX-style h1: # Title
            if not h1_removed and line.strip().startswith('# '):
                # Extract title for logging
                h1_title = line.strip()[2:].strip()
                # Skip this line (the h1)
                h1_removed = True
                i += 1
                # Skip any immediately following blank lines
                while i < len(lines) and not lines[i].strip():
                    i += 1
                continue

            # Check for Setext-style h1: Title\n===
            if not h1_removed and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == '=' for c in next_line):
                    # Extract title for logging
                    h1_title = line.strip()
                    # Skip both the title line and the === line
                    h1_removed = True
                    i += 2
                    # Skip any immediately following blank lines
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    continue

            # Keep this line
            result_lines.append(line)
            i += 1

        # Log when h1 is stripped
        if h1_removed and h1_title:
            logger.info(f"Stripped h1 heading: '{h1_title}'")

        return '\n'.join(result_lines)

    def _normalize_confluence_content(self, content):
        """Remove Confluence-added attributes and normalize whitespace.

        Args:
            content: The content string to normalize

        Returns:
            str: Normalized content string

        """
        if not content:
            return content
        import re
        # Remove ac:schema-version attributes
        content = re.sub(r'\s+ac:schema-version="[^"]*"', '', content)
        # Remove ac:macro-id attributes
        content = re.sub(r'\s+ac:macro-id="[^"]*"', '', content)
        # Normalize self-closing tags to explicit closing tags
        # Example: <ri:attachment ... /> becomes <ri:attachment ...></ri:attachment>
        content = re.sub(r'<(ri:attachment[^>]*)\s*/>', r'<\1></ri:attachment>', content)
        # Remove trailing spaces before closing > in tags
        content = re.sub(r'\s+>', '>', content)
        # Normalize line breaks between XML tags to single space
        content = re.sub(r'>\s+<', '><', content)
        # Normalize multiple spaces to single space
        content = re.sub(r'  +', ' ', content)
        return content.strip()

    def _convert_to_confluence_format(self, markdown, page_name):
        """Convert markdown to Confluence format and create temp file.

        This method processes markdown content by:
        1. Stripping h1 headings if strip_h1 option is enabled
        2. Converting image tags to Confluence format
        3. Converting markdown to Confluence HTML using Mistune
        4. Optionally saving debug HTML files

        Args:
            markdown (str): Markdown source to transform into Confluence storage format.
            page_name (str): Logical page name used when generating debug artifacts.

        Returns:
            str: The converted Confluence HTML content

        Note:
            This method modifies the markdown content in-place before conversion.

        """
        # Strip h1 if configured
        if self.config.get("strip_h1", False):
            markdown = self._strip_h1_from_markdown(markdown)
            if self.config["debug"]:
                logger.debug(f"strip_h1 enabled for page '{page_name}'")

        # Replace image tags for Confluence format
        new_markdown = re.sub(
            r'<img src="file:///tmp/', '<p><ac:image ac:height="350"><ri:attachment ri:filename="', markdown
        )
        new_markdown = re.sub(r'" style="page-break-inside: avoid;">', '"/></ac:image></p>', new_markdown)

        # Convert to Confluence format
        confluence_body = self.confluence_mistune(new_markdown)

        if self.config.get("debug_diff", False):
            logger.info(f"Converted Confluence content for '{page_name}' ({len(confluence_body)} chars)")
            logger.info(confluence_body)
            # Save debug HTML file to a temp directory with proper cleanup
            debug_dir = Path(tempfile.gettempdir()) / "mkdocs-to-confluence-debug"
            debug_dir.mkdir(exist_ok=True)
            debug_file = debug_dir / f"confluence_page_{page_name.replace(' ', '_')}.html"
            debug_file.write_text(confluence_body, encoding="utf-8")
            logger.debug(f"Debug HTML saved to: {debug_file}")

        return confluence_body

    def _ensure_parent_hierarchy(self, parent_chain):
        """Ensure parent page hierarchy exists in Confluence.

        Creates parent pages if they don't exist, starting from the root parent
        down to the direct parent. Handles arbitrary depth hierarchies.

        Args:
            parent_chain: List of parent page titles from root to direct parent.
                         Example: ["Home", "Getting Started", "Installation"]
                         The last element is the direct parent.

        Returns:
            int or None: The direct parent page ID, or None if it couldn't be created

        """
        if not parent_chain:
            logger.error("Empty parent chain provided. ABORTING!")
            return None

        # Track parent IDs as we traverse the hierarchy
        current_parent_id = None

        # Iterate through the parent chain, ensuring each level exists
        for i, parent_title in enumerate(parent_chain):
            parent_id = self.find_page_id(parent_title)

            if parent_id:
                # Parent exists, use it for the next level
                current_parent_id = parent_id
                # Track this parent page as synced
                self.synced_pages.add(parent_title)
                if self.config["debug"]:
                    logger.debug(f"Parent '{parent_title}' exists with ID: {parent_id}")
            else:
                # Parent doesn't exist, need to create it
                if i == 0:
                    # This is the root parent - it must exist!
                    logger.error(f"ROOT PARENT '{parent_title}' UNKNOWN. ABORTING!")
                    return None

                # Create the page under the previous parent
                if self.config["debug"]:
                    logger.debug(
                        f"Trying to ADD page '{parent_title}' to "
                        f"parent '{parent_chain[i-1]}' ID: {current_parent_id}"
                    )

                body = TEMPLATE_BODY.replace("TEMPLATE", parent_title)
                self.add_page(parent_title, current_parent_id, body)

                for item in MkdocsWithConfluence.tab_nav:
                    if parent_title in item:
                        logger.info(f"Mkdocs With Confluence: {item} *NEW PAGE*")

                # Wait for the newly created page to be available and get its ID
                if self.config["debug"]:
                    logger.debug(f"Waiting for newly created page '{parent_title}' to be available...")

                # Capture loop variable in lambda default argument to avoid late binding issue
                self.wait_until(
                    lambda title=parent_title: self.find_page_id(title),
                    interval=1,
                    timeout=20,
                    max_retries=3,
                )
                parent_id = self.find_page_id(parent_title)

                if not parent_id:
                    logger.error(f"Failed to create or retrieve parent page '{parent_title}'. ABORTING!")
                    return None

                # Track this newly created parent page as synced
                self.synced_pages.add(parent_title)
                current_parent_id = parent_id

        # Return the ID of the direct parent (last in the chain)
        return current_parent_id

    def _sync_page(self, page_title, parent_chain, confluence_body):
        """Synchronize a page to Confluence (create or update).

        This method handles the complete synchronization process for a single page,
        including determining whether to create a new page or update an existing one,
        validating parent relationships, comparing content changes, and performing
        the appropriate Confluence API operations.

        For existing pages:
        - Validates that the page has the correct parent
        - Fetches current content and compares with new content
        - Updates the page if content has changed
        - Logs appropriate status messages

        For new pages:
        - Ensures the parent page hierarchy exists
        - Creates the new page under the correct parent
        - Logs the creation status

        Args:
            page_title (str): The title of the page to sync
            parent_chain (list[str]): Ordered list of parent page titles from root
                to direct parent. Example: ["Home", "Getting Started", "Installation"]
            confluence_body (str): The Confluence-formatted HTML content for the page

        Returns:
            bool: True if sync was successful, False if aborted due to errors

        """
        page_id = self.find_page_id(page_title)

        # Extract direct parent from the chain (last element)
        direct_parent = parent_chain[-1] if parent_chain else None

        if page_id is not None:
            # Page exists - check if update is needed
            if self.config["debug"]:
                logger.debug(
                    f"JUST ONE STEP FROM UPDATE OF PAGE '{page_title}' \n"
                    f"CHECKING IF PARENT PAGE ON CONFLUENCE IS THE SAME AS HERE"
                )

            # Track parent pages in the hierarchy for existing pages
            for parent_title in parent_chain:
                self.synced_pages.add(parent_title)

            parent_name = self.find_parent_name_of_page(page_title)

            if parent_name == direct_parent:
                if self.config["debug"]:
                    logger.debug("Parents match. Continue...")
            else:
                if self.config["debug"]:
                    logger.debug(f"ERR, Parents does not match: '{direct_parent}' =/= '{parent_name}' Aborting...")
                return False

            # Fetch current content to check if update is needed
            current_content = self.get_page_content(page_id)

            if self.config.get("debug_diff", False) and current_content is not None:
                logger.info(f"Content comparison for '{page_title}':")
                logger.info(f"  - Current: {len(current_content)} chars, New: {len(confluence_body)} chars")

                # Write to temp files for detailed comparison
                import tempfile
                from pathlib import Path
                temp_dir = Path(tempfile.gettempdir()) / "confluence-debug"
                temp_dir.mkdir(exist_ok=True)
                safe_title = page_title.replace('/', '_').replace(' ', '_')
                current_file = temp_dir / f"{safe_title}_current.html"
                new_file = temp_dir / f"{safe_title}_new.html"
                current_normalized = temp_dir / f"{safe_title}_current_normalized.html"
                new_normalized = temp_dir / f"{safe_title}_new_normalized.html"
                current_file.write_text(current_content, encoding='utf-8')
                new_file.write_text(confluence_body, encoding='utf-8')
                current_normalized.write_text(self._normalize_confluence_content(current_content), encoding='utf-8')
                new_normalized.write_text(self._normalize_confluence_content(confluence_body), encoding='utf-8')
                logger.info(f"  - Debug files: {temp_dir}")
                logger.info(f"    diff '{current_normalized}' '{new_normalized}'")

            # Compare normalized content - only update if changed
            normalized_current = self._normalize_confluence_content(current_content) if current_content else None
            normalized_new = self._normalize_confluence_content(confluence_body)
            if normalized_current is not None and normalized_current == normalized_new:
                if self.config.get("debug_diff", False):
                    logger.info(f"Page '{page_title}' content unchanged. Skipping update.")
                logger.info(f"  * Mkdocs With Confluence: {page_title} - *NO CHANGE*")
                for i in MkdocsWithConfluence.tab_nav:
                    if page_title in i:
                        logger.info(f"Mkdocs With Confluence: {i} *NO CHANGE*")

                # Track synced page (even if unchanged)
                self.synced_pages.add(page_title)
            else:
                # Content has changed, perform update
                if self.config.get("debug_diff", False):
                    if current_content is None:
                        logger.info(f"Page '{page_title}' - Could not fetch current content, will update")
                    else:
                        logger.info(f"Page '{page_title}' - Content has changed, updating")
                self.update_page(page_title, confluence_body)
                for i in MkdocsWithConfluence.tab_nav:
                    if page_title in i:
                        logger.info(f"Mkdocs With Confluence: {i} *UPDATE*")

            # Track synced page
            self.synced_pages.add(page_title)
        else:
            # Page doesn't exist - create it
            if self.config["debug"]:
                logger.debug(
                    f"PAGE: {page_title}, PARENT CHAIN: {' > '.join(parent_chain)}"
                )

            # Ensure parent hierarchy exists
            parent_id = self._ensure_parent_hierarchy(parent_chain)
            if parent_id is None:
                return False

            # Retry logic for parent ID
            if parent_id is None:
                for i in range(11):
                    while parent_id is None:
                        try:
                            self.add_page(page_title, parent_id, confluence_body)
                        except requests.exceptions.HTTPError:
                            logger.error(
                                f"HTTP error on adding page. It probably occured due to "
                                f"parent ID('{parent_id}') page is not YET synced on server. Retry nb {i}/10..."
                            )
                            sleep(5)
                            parent_id = self.find_page_id(direct_parent)
                        break

            self.add_page(page_title, parent_id, confluence_body)

            logger.info(f"Trying to ADD page '{page_title}' to parent({direct_parent}) ID: {parent_id}")
            for i in MkdocsWithConfluence.tab_nav:
                if page_title in i:
                    logger.info(f"Mkdocs With Confluence: {i} *NEW PAGE*")

            # Track synced page
            self.synced_pages.add(page_title)

        # Add labels to page if configured (get page_id if we just created it)
        if self.config.get("page_label"):
            if page_id is None:
                page_id = self.find_page_id(page_title)
            if page_id is not None:
                self.add_page_labels(page_id, [self.config["page_label"]])

        return True

    def on_page_markdown(self, markdown: str, page: Any, config: Any, files: Any) -> str:
        """Process markdown content and publish to Confluence.

        Args:
            markdown (str): Markdown generated by MkDocs for the current page.
            page (mkdocs.structure.pages.Page): Page metadata within the nav tree.
            config (mkdocs.config.base.Config): Active MkDocs configuration.
            files (mkdocs.structure.files.Files): Collection of build file objects.

        Returns:
            str: Markdown that MkDocs should continue to render or return if syncing fails.

        """
        MkdocsWithConfluence._id += 1

        # Set up authentication based on auth_type
        if self.config["api_token"]:
            token = self.config["api_token"]
            if self.config["auth_type"] == "bearer":
                self.session.auth = BearerAuth(token)
                if self.config["debug"]:
                    logger.debug(f"Using OAuth Bearer token authentication for {self.config['username']}")
            else:
                # Use HTTP Basic Auth (default)
                # Convert None to empty string to avoid deprecation warning in requests 3.0.0
                username = self.config["username"] or ""
                if username == "":
                    logger.warning("Username is not configured. Check plugin configuration or environment variables.")
                if token == "":
                    logger.warning("API token is not configured. Check plugin configuration or environment variables.")
                self.session.auth = (username, token)
        else:
            # Convert None to empty string to avoid deprecation warning in requests 3.0.0
            username = self.config["username"] or ""
            password = self.config["password"] or ""
            if username == "":
                logger.warning("Username is not configured. Check plugin configuration or environment variables.")
            if password == "":
                logger.warning("Password is not configured. Check plugin configuration or environment variables.")
            self.session.auth = (username, password)

        if self.enabled:
            if self.simple_log is True:
                progress = "#" * MkdocsWithConfluence._id
                remaining = "-" * (self.flen - MkdocsWithConfluence._id)
                logger.info(
                    f"Mkdocs With Confluence: Page export progress: [{progress}{remaining}] "
                    f"({MkdocsWithConfluence._id} / {self.flen})"
                )

            if self.config["debug"]:
                logger.debug(f"\nHandling Page '{page.title}' (And Parent Nav Pages if necessary):\n")
            if not all(self.config_scheme):
                logger.error("YOU HAVE EMPTY VALUES IN YOUR CONFIG. ABORTING")
                return markdown

            try:
                # Resolve parent page hierarchy
                parent_chain = self._resolve_page_parents(page)

                # Extract attachments from markdown
                attachments = self._extract_attachments(markdown)

                # Convert markdown to Confluence format
                confluence_body = self._convert_to_confluence_format(markdown, page.title)

                if self.config["debug"]:
                    logger.debug(
                        f"\nUPDATING PAGE TO CONFLUENCE, DETAILS:\n"
                        f"HOST: {self.config['host_url']}\n"
                        f"SPACE: {self.config['space']}\n"
                        f"TITLE: {page.title}\n"
                        f"PARENT CHAIN: {' > '.join(parent_chain)}\n"
                        f"BODY: {confluence_body}\n"
                    )

                # Sync page to Confluence or add to exporter
                if self.dryrun and self.exporter:
                    # Add page to exporter queue for dry-run export
                    # For dry-run, pass direct parent (last in chain) if it's not the root
                    direct_parent = parent_chain[-1] if parent_chain else None
                    root_parent = parent_chain[0] if parent_chain else None
                    self.exporter.add_page(
                        title=page.title,
                        parent=direct_parent if direct_parent != root_parent else None,
                        space=self.config["space"],
                        confluence_body=confluence_body,
                        attachments=attachments,
                    )
                    logger.info(f"Mkdocs With Confluence: {page.title} - *QUEUED FOR EXPORT*")
                else:
                    # Normal mode: sync to Confluence (create or update)
                    sync_success = self._sync_page(page.title, parent_chain, confluence_body)
                    if not sync_success:
                        return markdown

                    if attachments:
                        self.page_attachments[page.title] = attachments

            except IndexError as e:
                if self.config["debug"]:
                    logger.debug(f"ERR({e}): Exception error!")
                return markdown

        return markdown

    def on_post_page(self, output: str, page: Any, config: Any) -> str:
        """Upload attachments after page is rendered.

        Args:
            output (str): Rendered HTML for the page.
            page (mkdocs.structure.pages.Page): Page metadata used for lookup.
            config (mkdocs.config.base.Config): Active MkDocs configuration.

        Returns:
            str: Rendered HTML that MkDocs should write to disk.

        """
        site_dir = config.get("site_dir")
        attachments = self.page_attachments.get(page.title, [])

        if self.config["debug"]:
            logger.debug(f"\nUPLOADING ATTACHMENTS TO CONFLUENCE FOR {page.title}, DETAILS:")
            logger.info(f"FILES: {attachments}  \n")
        for attachment in attachments:
            if self.config["debug"]:
                logger.debug(f"looking for {attachment} in {site_dir}")
            for p in Path(site_dir).rglob(f"*{attachment}"):
                self.add_or_update_attachment(page.title, p)
        return output

    def on_page_content(self, html: str, page: Any, config: Any, files: Any) -> str:
        """Process HTML content.

        Args:
            html (str): Rendered HTML output.
            page (mkdocs.structure.pages.Page): Page metadata.
            config (mkdocs.config.base.Config): Active MkDocs configuration.
            files (mkdocs.structure.files.Files): Collection of build file objects.

        Returns:
            str: HTML passed through without modification.

        """
        return html

    def on_post_build(self, config: Any) -> None:
        """Export all queued pages and handle orphaned pages after build completes.

        Args:
            config (mkdocs.config.base.Config): Active MkDocs configuration.

        """
        # Handle dry-run export
        if self.dryrun and self.exporter:
            logger.info("Mkdocs With Confluence: Exporting all pages to filesystem...")
            self.exporter.export_all()
            export_dir = Path(self.config["export_dir"])
            logger.info(f"Mkdocs With Confluence: Export complete! Files saved to {export_dir.absolute()}")
            return

        # Handle orphaned pages detection and cleanup (only when enabled and not in dryrun)
        if not self.enabled or self.dryrun:
            return

        # Get root parent page
        root_parent_name = self.config.get("parent_page_name") or self.config.get("space")
        if not root_parent_name:
            if self.config["debug"]:
                logger.debug("No root parent configured, skipping orphaned page detection")
            return

        root_parent_id = self.find_page_id(root_parent_name)
        if not root_parent_id:
            logger.warning(f"Could not find root parent page '{root_parent_name}', skipping orphaned page detection")
            return

        if self.config["debug"]:
            logger.debug(f"Checking for orphaned pages under '{root_parent_name}' (ID: {root_parent_id})")
            logger.debug(f"Synced pages during build: {sorted(self.synced_pages)}")

        # Get all pages in Confluence under the root parent
        try:
            confluence_pages = self.get_all_child_pages(root_parent_id)
        except Exception as e:
            logger.error(f"Failed to fetch Confluence pages: {e}")
            return

        if self.config["debug"]:
            confluence_titles_list = [page["title"] for page in confluence_pages]
            logger.debug(f"Pages in Confluence: {sorted(confluence_titles_list)}")

        # Find orphaned pages (in Confluence but not in synced_pages)
        confluence_titles = {page["title"] for page in confluence_pages}
        orphaned_titles = confluence_titles - self.synced_pages

        # Filter out pages in keep_pages list
        keep_pages = set(self.config.get("keep_pages", []))
        orphaned_titles = orphaned_titles - keep_pages

        if not orphaned_titles:
            logger.info("Mkdocs With Confluence: No orphaned pages found")
            return

        # Always warn about orphaned pages
        logger.warning(f"Mkdocs With Confluence: Found {len(orphaned_titles)} orphaned page(s) in Confluence:")
        for title in sorted(orphaned_titles):
            logger.warning(f"  - {title}")

        # Delete orphaned pages if cleanup is enabled
        if self.config.get("cleanup_orphaned_pages", False):
            logger.info("Mkdocs With Confluence: Cleanup enabled, deleting orphaned pages...")
            deleted_count = 0
            for page in confluence_pages:
                if page["title"] in orphaned_titles:
                    try:
                        self.delete_page(page["id"])
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete page '{page['title']}': {e}")

            logger.info(f"Mkdocs With Confluence: Deleted {deleted_count} orphaned page(s)")
        else:
            logger.info("Mkdocs With Confluence: Run with 'cleanup_orphaned_pages: true' to delete them")

    def __get_page_url(self, section):
        """Extract page URL from section string.

        Args:
            section (str): String representation of the navigation section entry.

        Returns:
            str or None: Local page URL when present, otherwise None.

        """
        match = re.search("url='(.*)'\\)", section)
        if match:
            return match.group(1)[:-1] + ".md"
        logger.warning(f"Could not extract page URL from: {section}")
        return None

    def __get_page_name(self, section):
        """Extract page name from section string.

        Args:
            section (str): String representation of the navigation section entry.

        Returns:
            str or None: Basename of the page when present, otherwise None.

        """
        match = re.search("url='(.*)'\\)", section)
        if match:
            return os.path.basename(match.group(1)[:-1])
        logger.warning(f"Could not extract page name from: {section}")
        return None

    def __get_section_name(self, section):
        """Extract section name from section string.

        Args:
            section (str): String representation of the navigation section entry.

        Returns:
            str or None: Section name when present, otherwise None.

        """
        if self.config["debug"]:
            logger.debug(f"SECTION name: {section}")
        match = re.search("url='(.*)'\\/", section)
        if match:
            return os.path.basename(match.group(1)[:-1])
        logger.warning(f"Could not extract section name from: {section}")
        return None

    def __get_section_title(self, section):
        """Extract section title from section string.

        Args:
            section (str): String representation of the navigation section entry.

        Returns:
            str or None: Section title when present, otherwise None.

        """
        if self.config["debug"]:
            logger.debug(f"SECTION title: {section}")
        try:
            r = re.search("Section\\(title='(.*)'\\)", section)
            if r:
                return r.group(1)
            # If regex doesn't match, try to get section name as fallback
            name = self.__get_section_name(section)
            if name:
                logger.info(f"WRN    - Section '{name}' doesn't exist in the mkdocs.yml nav section!")
                return name
            # Last resort - return None or a default
            logger.warning(f"Could not extract section title from: {section}")
            return None
        except (AttributeError, TypeError) as e:
            name = self.__get_section_name(section)
            if name:
                logger.info(f"WRN    - Section '{name}' doesn't exist in the mkdocs.yml nav section!")
                return name
            logger.warning(f"Error extracting section title: {e}")
            return None

    def __get_page_title(self, section):
        """Extract page title from section string.

        Args:
            section (str): String representation of the navigation section entry.

        Returns:
            str or None: Page title when present, otherwise None.

        """
        try:
            r = re.search("\\s*Page\\(title='(.*)',", section)
            if r:
                return r.group(1)
            # If regex doesn't match, try page URL as fallback
            name = self.__get_page_url(section)
            if name:
                logger.info(f"WRN    - Page '{name}' doesn't exist in the mkdocs.yml nav section!")
                return name
            return None
        except (AttributeError, TypeError) as e:
            name = self.__get_page_url(section)
            if name:
                logger.info(f"WRN    - Page '{name}' doesn't exist in the mkdocs.yml nav section!")
                return name
            logger.warning(f"Error extracting page title: {e}")
            return None

    # Adapted from
    def get_file_sha1(self, file_path: str) -> str:
        """Calculate SHA1 hash of file.

        Args:
            file_path (str or Path): Path to the file on disk.

        Returns:
            str: Hexadecimal SHA1 digest used to tag attachment versions.

        """
        hash_sha1 = hashlib.sha1()  # noqa: S324  # nosec B324  # SHA1 for file versioning, not security
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()

    def add_or_update_attachment(self, page_name: str, filepath: str) -> None:
        """Add or update attachment on Confluence page.

        Args:
            page_name (str): Title of the page that owns the attachment.
            filepath (str or Path): File to upload or compare against existing attachments.

        """
        filename = os.path.basename(filepath)

        page_id = self.find_page_id(page_name)
        if page_id:
            file_hash = self.get_file_sha1(filepath)
            attachment_message = f"MKDocsWithConfluence [v{file_hash}]"
            existing_attachment = self.get_attachment(page_id, filepath)
            if existing_attachment:
                file_hash_regex = re.compile(r"\[v([a-f0-9]{40})]$")
                existing_match = file_hash_regex.search(existing_attachment["version"]["message"])
                if existing_match is not None and existing_match.group(1) == file_hash:
                    # Attachment exists and hash matches - skip
                    logger.info(f"  * Attachment: {filename} - *NO CHANGE*")
                else:
                    # Hash mismatch - update needed
                    logger.info(f"  * Attachment: {filename} - *UPDATE*")
                    self.update_attachment(page_id, filepath, existing_attachment, attachment_message)
            else:
                # Attachment doesn't exist - create it
                logger.info(f"  * Attachment: {filename} - *NEW*")
                self.create_attachment(page_id, filepath, attachment_message)
        else:
            if self.config["debug"]:
                logger.info("PAGE DOES NOT EXISTS")

    def get_attachment(self, page_id: str, filepath: str) -> dict[str, Any] | None:
        """Get existing attachment from Confluence page.

        Args:
            page_id (str): Identifier of the Confluence page.
            filepath (str or Path): Path whose filename should be matched remotely.

        Returns:
            dict or None: Attachment metadata when found, otherwise None.

        """
        name = os.path.basename(filepath)
        if self.config["debug"]:
            logger.info(f" * Mkdocs With Confluence: Get Attachment: PAGE ID: {page_id}, FILE: {filepath}")

        url = self.config["host_url"] + "/" + page_id + "/child/attachment"
        headers = {"X-Atlassian-Token": "no-check"}  # no content-type here!
        if self.config["debug"]:
            logger.info(f"URL: {url}")

        r = self._safe_request(
            "get", url, f"getting attachment '{name}'",
            headers=headers, params={"filename": name, "expand": "version"}
        )
        if r is None:
            return None
        with nostdout():
            response_json = r.json()
        if response_json["size"]:
            return response_json["results"][0]

    def update_attachment(self, page_id, filepath, existing_attachment, message):
        """Update existing attachment on Confluence page.

        Args:
            page_id (str): Identifier of the Confluence page.
            filepath (str or Path): Local file whose contents replace the attachment.
            existing_attachment (dict): Metadata returned from get_attachment.
            message (str): Version comment displayed in Confluence history.

        """
        if self.config["debug"]:
            logger.info(f" * Mkdocs With Confluence: Update Attachment: PAGE ID: {page_id}, FILE: {filepath}")

        url = self.config["host_url"] + "/" + page_id + "/child/attachment/" + existing_attachment["id"] + "/data"
        headers = {"X-Atlassian-Token": "no-check"}  # no content-type here!

        if self.config["debug"]:
            logger.info(f"URL: {url}")

        filename = os.path.basename(filepath)

        # determine content-type
        content_type, encoding = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = "multipart/form-data"

        if not self.dryrun:
            with open(Path(filepath), "rb") as file_handle:
                files = {"file": (filename, file_handle, content_type), "comment": message}
                r = self._safe_request("post", url, f"updating attachment '{filename}'", headers=headers, files=files)
                if r is None:
                    return
                logger.info(r.json())
                if r.status_code == 200:
                    logger.info("OK!")
                else:
                    logger.error("ERR!")

    def create_attachment(self, page_id, filepath, message):
        """Create new attachment on Confluence page.

        Args:
            page_id (str): Identifier of the Confluence page.
            filepath (str or Path): Local file to upload as a new attachment.
            message (str): Version comment displayed in Confluence history.

        """
        if self.config["debug"]:
            logger.info(f" * Mkdocs With Confluence: Create Attachment: PAGE ID: {page_id}, FILE: {filepath}")

        url = self.config["host_url"] + "/" + page_id + "/child/attachment"
        headers = {"X-Atlassian-Token": "no-check"}  # no content-type here!

        if self.config["debug"]:
            logger.info(f"URL: {url}")

        filename = os.path.basename(filepath)

        # determine content-type
        content_type, encoding = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = "multipart/form-data"

        if not self.dryrun:
            with open(filepath, "rb") as file_handle:
                files = {"file": (filename, file_handle, content_type), "comment": message}
                r = self._safe_request("post", url, f"creating attachment '{filename}'", headers=headers, files=files)
                if r is None:
                    return
                logger.info(r.json())
                if r.status_code == 200:
                    logger.info("OK!")
                else:
                    logger.error("ERR!")

    def find_page_id(self, page_name: str) -> str | None:
        """Find Confluence page ID by name.

        Args:
            page_name (str): Title of the page to locate.

        Returns:
            str or None: Page identifier when found, otherwise None.

        """
        if self.config["debug"]:
            logger.info(f"  * Mkdocs With Confluence: Find Page ID: PAGE NAME: {page_name}")

        name_confl = page_name.replace(" ", "+")
        url = (
            f"{self.config['host_url']}?title={name_confl}"
            f"&spaceKey={self.config['space']}&expand=history"
        )

        if self.config["debug"]:
            logger.info(f"URL: {url}")

        r = self._safe_request("get", url, f"finding page ID for '{page_name}'")
        if r is None:
            return None
        with nostdout():
            response_json = r.json()
        if response_json["results"]:
            if self.config["debug"]:
                logger.info(f"ID: {response_json['results'][0]['id']}")
            return response_json["results"][0]["id"]
        else:
            if self.config["debug"]:
                logger.info("PAGE DOES NOT EXIST")
            return None

    def get_page_content(self, page_id: str) -> str | None:
        """Fetch the current content of a page from Confluence.

        Args:
            page_id: The Confluence page ID

        Returns:
            str or None: The page content in storage format, or None if fetch failed

        """
        if self.config["debug"]:
            logger.info(f"Fetching current content for page ID: {page_id}")
        url = self.config["host_url"] + "/" + page_id + "?expand=body.storage"
        r = self._safe_request("get", url, f"fetching content for page ID '{page_id}'")
        if r is None:
            if self.config["debug"]:
                logger.info("Failed to fetch page content (request returned None)")
            return None
        try:
            with nostdout():
                response_json = r.json()
            content = response_json.get("body", {}).get("storage", {}).get("value")
            if self.config["debug"]:
                logger.info(f"Fetched content length: {len(content) if content else 0} characters")
            return content
        except Exception as e:
            if self.config["debug"]:
                logger.info(f"Error parsing page content: {e}")
            return None

    def add_page(self, page_name, parent_page_id, page_content_in_storage_format):
        """Create new page in Confluence.

        Args:
            page_name (str): Title for the new page.
            parent_page_id (str): Identifier of the parent page.
            page_content_in_storage_format (str): Body content in Confluence storage format.

        """
        logger.info(f"  * Mkdocs With Confluence: {page_name} - *NEW PAGE*")

        if self.config["debug"]:
            logger.info(f" * Mkdocs With Confluence: Adding Page: PAGE NAME: {page_name}, parent ID: {parent_page_id}")
        url = self.config["host_url"] + "/"
        if self.config["debug"]:
            logger.info(f"URL: {url}")
        headers = {"Content-Type": "application/json"}
        space = self.config["space"]
        data = {
            "type": "page",
            "title": page_name,
            "space": {"key": space},
            "ancestors": [{"id": parent_page_id}],
            "body": {"storage": {"value": page_content_in_storage_format, "representation": "storage"}},
        }
        if self.config["debug"]:
            logger.info(f"DATA: {data}")
        if not self.dryrun:
            r = self._safe_request("post", url, f"creating page '{page_name}'", json=data, headers=headers)
            if r is None:
                return
            if r.status_code == 200:
                if self.config["debug"]:
                    logger.info("OK!")
            else:
                if self.config["debug"]:
                    logger.error("ERR!")

    def update_page(self, page_name, page_content_in_storage_format):
        """Update existing page in Confluence.

        Args:
            page_name (str): Title of the page to update.
            page_content_in_storage_format (str): Body content in Confluence storage format.

        """
        page_id = self.find_page_id(page_name)
        logger.info(f"  * Mkdocs With Confluence: {page_name} - *UPDATE*")
        if self.config["debug"]:
            logger.info(f" * Mkdocs With Confluence: Update PAGE ID: {page_id}, PAGE NAME: {page_name}")
        if page_id:
            page_version = self.find_page_version(page_name)
            if page_version is None:
                logger.error(f"Cannot update page '{page_name}': unable to retrieve version")
                return
            page_version = page_version + 1
            url = self.config["host_url"] + "/" + page_id
            if self.config["debug"]:
                logger.info(f"URL: {url}")
            headers = {"Content-Type": "application/json"}
            space = self.config["space"]
            data = {
                "id": page_id,
                "title": page_name,
                "type": "page",
                "space": {"key": space},
                "body": {"storage": {"value": page_content_in_storage_format, "representation": "storage"}},
                "version": {"number": page_version},
            }

            if not self.dryrun:
                r = self._safe_request("put", url, f"updating page '{page_name}'", json=data, headers=headers)
                if r is None:
                    return
                if r.status_code == 200:
                    if self.config["debug"]:
                        logger.info("OK!")
                else:
                    if self.config["debug"]:
                        logger.error("ERR!")
        else:
            if self.config["debug"]:
                logger.info("PAGE DOES NOT EXIST YET!")

    def find_page_version(self, page_name: str) -> int | None:
        """Find current version number of Confluence page.

        Args:
            page_name (str): Title of the page to inspect.

        Returns:
            int or None: Latest version number, or None when the page is missing.

        """
        if self.config["debug"]:
            logger.info(f"  * Mkdocs With Confluence: Find PAGE VERSION, PAGE NAME: {page_name}")
        name_confl = page_name.replace(" ", "+")
        url = self.config["host_url"] + "?title=" + name_confl + "&spaceKey=" + self.config["space"] + "&expand=version"
        r = self._safe_request("get", url, f"finding page version for '{page_name}'")
        if r is None:
            return None
        with nostdout():
            response_json = r.json()
        if response_json["results"] and len(response_json["results"]) > 0:
            if self.config["debug"]:
                logger.info(f"VERSION: {response_json['results'][0]['version']['number']}")
            return response_json["results"][0]["version"]["number"]
        else:
            if self.config["debug"]:
                logger.info("PAGE DOES NOT EXISTS")
            return None

    def find_parent_name_of_page(self, name: str) -> str | None:
        """Find parent page name of given Confluence page.

        Args:
            name (str): Title of the page whose parent is requested.

        Returns:
            str or None: Title of the direct parent page, or None when unavailable.

        """
        if self.config["debug"]:
            logger.info(f"  * Mkdocs With Confluence: Find PARENT OF PAGE, PAGE NAME: {name}")
        idp = self.find_page_id(name)
        if idp is None:
            return None
        url = self.config["host_url"] + "/" + idp + "?expand=ancestors"

        r = self._safe_request("get", url, f"finding parent of page '{name}'")
        if r is None:
            return None
        with nostdout():
            response_json = r.json()
        if response_json and "ancestors" in response_json and len(response_json["ancestors"]) > 0:
            if self.config["debug"]:
                logger.info(f"PARENT NAME: {response_json['ancestors'][-1]['title']}")
            return response_json["ancestors"][-1]["title"]
        else:
            if self.config["debug"]:
                logger.info("PAGE DOES NOT HAVE PARENT")
            return None

    def get_all_child_pages(self, parent_id: str) -> list[dict[str, Any]]:
        """Get all child pages recursively under a parent page.

        Args:
            parent_id: The ID of the parent page

        Returns:
            List of page dictionaries with 'id' and 'title' keys

        """
        all_pages: list[dict[str, Any]] = []
        url = self.config["host_url"] + "/" + parent_id + "/child/page"
        params = {"limit": 100}  # Confluence API default limit is 25

        if self.config["debug"]:
            logger.debug(f"Fetching child pages for parent ID: {parent_id}")

        while url:
            r = self._safe_request("get", url, f"fetching child pages for parent ID '{parent_id}'", params=params)
            if r is None:
                break

            with nostdout():
                response_json = r.json()

            if "results" in response_json:
                for page in response_json["results"]:
                    page_info = {"id": page["id"], "title": page["title"]}
                    all_pages.append(page_info)

                    if self.config["debug"]:
                        logger.debug(f"Found child page: {page['title']} (ID: {page['id']})")

                    # Recursively get children of this page
                    child_pages = self.get_all_child_pages(page["id"])
                    all_pages.extend(child_pages)

            # Handle pagination
            if "next" in response_json.get("_links", {}):
                url = self.config["host_url"].rsplit("/content", 1)[0] + response_json["_links"]["next"]
                params = {}  # params are in the URL already
            else:
                break

        return all_pages

    def add_page_labels(self, page_id: str, labels: list[str]) -> None:
        """Add labels to a Confluence page.

        Args:
            page_id: The ID of the page
            labels: List of label names to add

        """
        if not labels:
            return

        url = self.config["host_url"] + "/" + page_id + "/label"
        headers = {"Content-Type": "application/json"}
        data = [{"name": label, "prefix": "global"} for label in labels]

        if self.config["debug"]:
            logger.debug(f"Adding labels {labels} to page ID: {page_id}")

        if not self.dryrun:
            r = self._safe_request("post", url, f"adding labels to page ID '{page_id}'", json=data, headers=headers)
            if r is not None and self.config["debug"]:
                logger.debug(f"Labels added successfully to page ID: {page_id}")

    def delete_page(self, page_id: str) -> None:
        """Delete a Confluence page.

        Args:
            page_id: The ID of the page to delete

        """
        url = self.config["host_url"] + "/" + page_id

        if self.config["debug"]:
            logger.debug(f"Deleting page ID: {page_id}")

        if not self.dryrun:
            r = self._safe_request("delete", url, f"deleting page ID '{page_id}'")
            if r is not None:
                logger.info(f"Deleted page ID: {page_id}")
            else:
                logger.error(f"Failed to delete page ID: {page_id}")

    def wait_until(
        self, condition: Callable[[], bool] | bool, interval: float = 0.1, timeout: int = 10, max_retries: int = 3
    ) -> bool:
        """Wait until a condition is met, with retry mechanism.

        Args:
            condition: The condition to wait for (can be a boolean or callable)
            interval: Time between checks in seconds
            timeout: Maximum time to wait in seconds
            max_retries: Maximum number of retries if condition is not met

        Returns:
            True if condition is met, False otherwise

        """
        for retry in range(max_retries):
            start = time.time()
            while time.time() - start < timeout:
                # Evaluate condition - if it's callable, call it; otherwise check truthiness
                result = condition() if callable(condition) else condition
                if result:
                    return True
                time.sleep(interval)

            if retry < max_retries - 1:
                logger.info(f"Condition not met, retrying ({retry+1}/{max_retries})...")

        logger.error(f"Condition not met after {max_retries} retries with {timeout}s timeout")
        return False
