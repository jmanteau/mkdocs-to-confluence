"""MkDocs plugin for publishing to Confluence."""

import contextlib
import hashlib
import logging
import mimetypes
import os
import re
import shutil
import sys
import tempfile
import time
from os import environ
from pathlib import Path
from time import sleep

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
        """Initialize with bearer token."""
        self.token = token

    def __call__(self, r):
        """Apply Bearer token to request headers."""
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


@contextlib.contextmanager
def nostdout():
    """Suppress stdout temporarily."""
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
        ("dryrun", config_options.Type(bool, default=False)),
        ("export_dir", config_options.Type(str, default="confluence-export")),
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
        """Build navigation structure from MkDocs nav."""
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
        """Count documentation pages."""
        pages = files.documentation_pages()
        self.flen = len(pages)
        logger.info(f"Number of files in directory tree: {self.flen}")
        if self.flen == 0:
            logger.error("No documentation pages in directory tree, please add at least one!")

    def on_post_template(self, output_content, template_name, config):
        """Configure logging mode based on verbosity settings."""
        if self.config["verbose"] is False and self.config["debug"] is False:
            self.simple_log = True
            logger.info("Mkdocs With Confluence: Start exporting markdown pages... (simple logging)")
        else:
            self.simple_log = False

    def on_config(self, config):
        """Configure plugin based on environment and settings."""
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

        if "enabled_if_env" in self.config:
            env_name = self.config["enabled_if_env"]
            if env_name:
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
                self.enabled = True
            else:
                logger.warning(
                    "Mkdocs With Confluence: Exporting MKDOCS pages to Confluence turned OFF: "
                    f"(set environment variable {env_name} to 1 to enable)"
                )
                return
        else:
            logger.info("Mkdocs With Confluence: Exporting MKDOCS pages to Confluence turned ON by default!")
            self.enabled = True

    def _resolve_page_parents(self, page):
        """Resolve parent page hierarchy for a given page.

        Args:
            page: The MkDocs page object

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
        """Extract image attachments from markdown content.

        Args:
            markdown: The markdown content string

        Returns:
            list: List of attachment file paths found in the markdown

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

    def _convert_to_confluence_format(self, markdown, page_name):
        """Convert markdown to Confluence format and create temp file.

        Args:
            markdown: The markdown content to convert
            page_name: The name of the page for temp file naming

        Returns:
            tuple: (confluence_body, temp_file_path) where:
                - confluence_body: Converted Confluence HTML content
                - temp_file_path: Path to the temporary file created

        """
        # Replace image tags for Confluence format
        new_markdown = re.sub(
            r'<img src="file:///tmp/', '<p><ac:image ac:height="350"><ri:attachment ri:filename="', markdown
        )
        new_markdown = re.sub(r'" style="page-break-inside: avoid;">', '"/></ac:image></p>', new_markdown)

        # Convert to Confluence format
        confluence_body = self.confluence_mistune(new_markdown)

        if self.config["debug"]:
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

                self.wait_until(lambda: self.find_page_id(parent_title), interval=1, timeout=20, max_retries=3)
                parent_id = self.find_page_id(parent_title)

                if not parent_id:
                    logger.error(f"Failed to create or retrieve parent page '{parent_title}'. ABORTING!")
                    return None

                current_parent_id = parent_id

        # Return the ID of the direct parent (last in the chain)
        return current_parent_id

    def _sync_page(self, page_title, parent_chain, confluence_body):
        """Synchronize a page to Confluence (create or update).

        Args:
            page_title: Title of the page to sync
            parent_chain: List of parent page titles from root to direct parent
            confluence_body: The Confluence-formatted HTML content

        Returns:
            bool: True if sync was successful, False if aborted

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

            # Normalize content for comparison (remove Confluence-added metadata)
            def normalize_confluence_content(content):
                """Remove Confluence-added attributes and normalize whitespace."""
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

            if self.config["debug"] and current_content is not None:
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
                current_normalized.write_text(normalize_confluence_content(current_content), encoding='utf-8')
                new_normalized.write_text(normalize_confluence_content(confluence_body), encoding='utf-8')
                logger.info(f"  - Debug files: {temp_dir}")
                logger.info(f"    diff '{current_normalized}' '{new_normalized}'")

            # Compare normalized content - only update if changed
            if current_content is not None and normalize_confluence_content(current_content) == normalize_confluence_content(confluence_body):
                if self.config["debug"]:
                    logger.info(f"Page '{page_title}' content unchanged. Skipping update.")
                logger.info(f"  * Mkdocs With Confluence: {page_title} - *NO CHANGE*")
                for i in MkdocsWithConfluence.tab_nav:
                    if page_title in i:
                        logger.info(f"Mkdocs With Confluence: {i} *NO CHANGE*")
            else:
                # Content has changed, perform update
                if self.config["debug"]:
                    if current_content is None:
                        logger.info(f"Page '{page_title}' - Could not fetch current content, will update")
                    else:
                        logger.info(f"Page '{page_title}' - Content has changed, updating")
                self.update_page(page_title, confluence_body)
                for i in MkdocsWithConfluence.tab_nav:
                    if page_title in i:
                        logger.info(f"Mkdocs With Confluence: {i} *UPDATE*")
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

        return True

    def on_page_markdown(self, markdown, page, config, files):
        """Process markdown content and publish to Confluence."""
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
                self.session.auth = (self.config["username"], token)
        else:
            self.session.auth = (self.config["username"], self.config["password"])

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

    def on_post_page(self, output, page, config):
        """Upload attachments after page is rendered."""
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

    def on_page_content(self, html, page, config, files):
        """Process HTML content."""
        return html

    def on_post_build(self, config):
        """Export all queued pages after build completes."""
        if self.dryrun and self.exporter:
            logger.info("Mkdocs With Confluence: Exporting all pages to filesystem...")
            self.exporter.export_all()
            export_dir = Path(self.config["export_dir"])
            logger.info(f"Mkdocs With Confluence: Export complete! Files saved to {export_dir.absolute()}")

    def __get_page_url(self, section):
        """Extract page URL from section string."""
        match = re.search("url='(.*)'\\)", section)
        if match:
            return match.group(1)[:-1] + ".md"
        logger.warning(f"Could not extract page URL from: {section}")
        return None

    def __get_page_name(self, section):
        """Extract page name from section string."""
        match = re.search("url='(.*)'\\)", section)
        if match:
            return os.path.basename(match.group(1)[:-1])
        logger.warning(f"Could not extract page name from: {section}")
        return None

    def __get_section_name(self, section):
        """Extract section name from section string."""
        if self.config["debug"]:
            logger.debug(f"SECTION name: {section}")
        match = re.search("url='(.*)'\\/", section)
        if match:
            return os.path.basename(match.group(1)[:-1])
        logger.warning(f"Could not extract section name from: {section}")
        return None

    def __get_section_title(self, section):
        """Extract section title from section string."""
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
        """Extract page title from section string."""
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

    # Adapted from https://stackoverflow.com/a/3431838
    def get_file_sha1(self, file_path):
        """Calculate SHA1 hash of file."""
        hash_sha1 = hashlib.sha1()  # noqa: S324  # nosec B324  # SHA1 for file versioning, not security
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()

    def add_or_update_attachment(self, page_name, filepath):
        """Add or update attachment on Confluence page."""
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

    def get_attachment(self, page_id, filepath):
        """Get existing attachment from Confluence page."""
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
        """Update existing attachment on Confluence page."""
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
        """Create new attachment on Confluence page."""
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

    def find_page_id(self, page_name):
        """Find Confluence page ID by name."""
        if self.config["debug"]:
            logger.info(f"  * Mkdocs With Confluence: Find Page ID: PAGE NAME: {page_name}")
            name_confl = page_name.replace(" ", "+")
            url = self.config["host_url"] + "?title=" + name_confl + "&spaceKey=" + self.config["space"] + "&expand=history"
            logger.info(f"URL: {url}")
        else:
            name_confl = page_name.replace(" ", "+")
            url = self.config["host_url"] + "?title=" + name_confl + "&spaceKey=" + self.config["space"] + "&expand=history"

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

    def get_page_content(self, page_id):
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
        """Create new page in Confluence."""
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
        """Update existing page in Confluence."""
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

    def find_page_version(self, page_name):
        """Find current version number of Confluence page."""
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

    def find_parent_name_of_page(self, name):
        """Find parent page name of given Confluence page."""
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

    def wait_until(self, condition, interval=0.1, timeout=10, max_retries=3):
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
                print(f"INFO    - Condition not met, retrying ({retry+1}/{max_retries})...")

        print(f"ERROR   - Condition not met after {max_retries} retries with {timeout}s timeout")
        return False
