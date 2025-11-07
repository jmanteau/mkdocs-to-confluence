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
from mkdocs_to_confluence._vendor.md2cf.confluence_renderer import ConfluenceRenderer
from requests.auth import AuthBase

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
        else:
            self.dryrun = False

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
            tuple: (parent, parent1, main_parent) where:
                - parent: Direct parent page title
                - parent1: Second-level parent page title
                - main_parent: Root parent from config or space
        """
        if self.config["debug"]:
            logger.debug("Get section first parent title...: ")

        try:
            parent = self.__get_section_title(page.ancestors[0].__repr__())
        except IndexError as e:
            if self.config["debug"]:
                logger.debug(
                    f"WRN({e}): No first parent! Assuming "
                    f"{self.config['parent_page_name']}..."
                )
            parent = None

        if self.config["debug"]:
            logger.debug(f"{parent}")

        if not parent:
            parent = self.config["parent_page_name"]

        # Determine main parent
        if self.config["parent_page_name"] is not None:
            main_parent = self.config["parent_page_name"]
        else:
            main_parent = self.config["space"]

        # Get second parent
        if self.config["debug"]:
            logger.debug("Get section second parent title...: ")

        try:
            parent1 = self.__get_section_title(page.ancestors[1].__repr__())
        except IndexError as e:
            if self.config["debug"]:
                logger.debug(
                    f"ERR({e}) No second parent! Assuming "
                    f"second parent is main parent: {main_parent}..."
                )
            parent1 = None

        if self.config["debug"]:
            logger.info(f"{parent}")

        if not parent1:
            parent1 = main_parent
            if self.config["debug"]:
                logger.debug(
                    f"ONLY ONE PARENT FOUND. ASSUMING AS A "
                    f"FIRST NODE after main parent config {main_parent}"
                )

        if self.config["debug"]:
            logger.debug(f"PARENT0: {parent}, PARENT1: {parent1}, MAIN PARENT: {main_parent}")

        return parent, parent1, main_parent

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

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(confluence_body)
            f.flush()  # Explicitly flush buffer to disk to prevent 0-byte files
            temp_name = f.name

        if self.config["debug"]:
            logger.info(confluence_body)

        # Create a copy with a descriptive name
        new_name = "confluence_page_" + page_name.replace(" ", "_") + ".html"
        shutil.copy(temp_name, new_name)

        return confluence_body, temp_name

    def _ensure_parent_hierarchy(self, parent, parent1, main_parent):
        """Ensure parent page hierarchy exists in Confluence.

        Creates parent pages if they don't exist, starting from the main parent
        down to the immediate parent.

        Args:
            parent: Direct parent page title
            parent1: Second-level parent page title
            main_parent: Root parent page title

        Returns:
            int or None: The parent page ID, or None if it couldn't be created
        """
        parent_id = self.find_page_id(parent)
        self.wait_until(parent_id, 1, 20)
        second_parent_id = self.find_page_id(parent1)
        self.wait_until(second_parent_id, 1, 20)
        main_parent_id = self.find_page_id(main_parent)

        if not parent_id:
            if not second_parent_id:
                main_parent_id = self.find_page_id(main_parent)
                if not main_parent_id:
                    logger.error("MAIN PARENT UNKNOWN. ABORTING!")
                    return None

                if self.config["debug"]:
                    logger.debug(
                        f"Trying to ADD page '{parent1}' to "
                        f"main parent({main_parent}) ID: {main_parent_id}"
                    )
                body = TEMPLATE_BODY.replace("TEMPLATE", parent1)
                self.add_page(parent1, main_parent_id, body)
                for i in MkdocsWithConfluence.tab_nav:
                    if parent1 in i:
                        logger.info(f"Mkdocs With Confluence: {i} *NEW PAGE*")
                time.sleep(1)

            if self.config["debug"]:
                logger.debug(
                    f"Trying to ADD page '{parent}' "
                    f"to parent1({parent1}) ID: {second_parent_id}"
                )
            body = TEMPLATE_BODY.replace("TEMPLATE", parent)
            self.add_page(parent, second_parent_id, body)
            for i in MkdocsWithConfluence.tab_nav:
                if parent in i:
                    logger.info(f"Mkdocs With Confluence: {i} *NEW PAGE*")
            time.sleep(1)

        return parent_id

    def _sync_page(self, page_title, parent, parent1, main_parent, confluence_body):
        """Synchronize a page to Confluence (create or update).

        Args:
            page_title: Title of the page to sync
            parent: Direct parent page title
            parent1: Second-level parent page title
            main_parent: Root parent page title
            confluence_body: The Confluence-formatted HTML content

        Returns:
            bool: True if sync was successful, False if aborted
        """
        page_id = self.find_page_id(page_title)

        if page_id is not None:
            # Page exists - update it
            if self.config["debug"]:
                logger.debug(
                    f"JUST ONE STEP FROM UPDATE OF PAGE '{page_title}' \n"
                    f"CHECKING IF PARENT PAGE ON CONFLUENCE IS THE SAME AS HERE"
                )

            parent_name = self.find_parent_name_of_page(page_title)

            if parent_name == parent:
                if self.config["debug"]:
                    logger.debug("Parents match. Continue...")
            else:
                if self.config["debug"]:
                    logger.debug(f"ERR, Parents does not match: '{parent}' =/= '{parent_name}' Aborting...")
                return False

            self.update_page(page_title, confluence_body)
            for i in MkdocsWithConfluence.tab_nav:
                if page_title in i:
                    logger.info(f"Mkdocs With Confluence: {i} *UPDATE*")
        else:
            # Page doesn't exist - create it
            if self.config["debug"]:
                logger.debug(
                    f"PAGE: {page_title}, PARENT0: {parent}, "
                    f"PARENT1: {parent1}, MAIN PARENT: {main_parent}"
                )

            # Ensure parent hierarchy exists
            parent_id = self._ensure_parent_hierarchy(parent, parent1, main_parent)
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
                            parent_id = self.find_page_id(parent)
                        break

            self.add_page(page_title, parent_id, confluence_body)

            logger.info(f"Trying to ADD page '{page_title}' to parent0({parent}) ID: {parent_id}")
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
                parent, parent1, main_parent = self._resolve_page_parents(page)

                # Extract attachments from markdown
                attachments = self._extract_attachments(markdown)

                # Convert markdown to Confluence format
                confluence_body, temp_name = self._convert_to_confluence_format(markdown, page.title)

                if self.config["debug"]:
                    logger.debug(
                        f"\nUPDATING PAGE TO CONFLUENCE, DETAILS:\n"
                        f"HOST: {self.config['host_url']}\n"
                        f"SPACE: {self.config['space']}\n"
                        f"TITLE: {page.title}\n"
                        f"PARENT: {parent}\n"
                        f"BODY: {confluence_body}\n"
                    )

                # Sync page to Confluence (create or update)
                sync_success = self._sync_page(page.title, parent, parent1, main_parent, confluence_body)
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
        logger.info(f"Mkdocs With Confluence * {page_name} *ADD/Update ATTACHMENT if required* {filepath}")
        if self.config["debug"]:
            logger.info(f" * Mkdocs With Confluence: Add Attachment: PAGE NAME: {page_name}, FILE: {filepath}")
        page_id = self.find_page_id(page_name)
        if page_id:
            file_hash = self.get_file_sha1(filepath)
            attachment_message = f"MKDocsWithConfluence [v{file_hash}]"
            existing_attachment = self.get_attachment(page_id, filepath)
            if existing_attachment:
                file_hash_regex = re.compile(r"\[v([a-f0-9]{40})]$")
                existing_match = file_hash_regex.search(existing_attachment["version"]["message"])
                if existing_match is not None and existing_match.group(1) == file_hash:
                    if self.config["debug"]:
                        logger.info(
                            f" * Mkdocs With Confluence * {page_name} * Existing attachment skipping * {filepath}"
                        )
                else:
                    self.update_attachment(page_id, filepath, existing_attachment, attachment_message)
            else:
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

        r = self.session.get(url, headers=headers, params={"filename": name, "expand": "version"})
        r.raise_for_status()
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
                r = self.session.post(url, headers=headers, files=files)
                r.raise_for_status()
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
                r = self.session.post(url, headers=headers, files=files)
                logger.info(r.json())
                r.raise_for_status()
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
        if self.config["debug"]:
            logger.info(f"URL: {url}")
        r = self.session.get(url)
        r.raise_for_status()
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
            r = self.session.post(url, json=data, headers=headers)
            r.raise_for_status()
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
                r = self.session.put(url, json=data, headers=headers)
                r.raise_for_status()
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
        r = self.session.get(url)
        r.raise_for_status()
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
        url = self.config["host_url"] + "/" + idp + "?expand=ancestors"

        r = self.session.get(url)
        r.raise_for_status()
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
            condition: The condition to wait for
            interval: Time between checks in seconds
            timeout: Maximum time to wait in seconds
            max_retries: Maximum number of retries if condition is not met

        Returns:
            True if condition is met, False otherwise
        """
        for retry in range(max_retries):
            start = time.time()
            while time.time() - start < timeout:
                if condition:
                    return True
                time.sleep(interval)

            if retry < max_retries - 1:
                print(f"INFO    - Condition not met, retrying ({retry+1}/{max_retries})...")

        print(f"ERROR   - Condition not met after {max_retries} retries with {timeout}s timeout")
        return False
