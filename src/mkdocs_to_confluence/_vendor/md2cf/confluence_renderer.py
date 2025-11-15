import re
import uuid
from pathlib import Path
from typing import Any, List, NamedTuple, Optional
from urllib.parse import unquote, urlparse

import mistune


def convert_markdown_anchor_to_confluence(markdown_anchor: str, page_title: str) -> str:
    """Convert a markdown-style anchor to Confluence's anchor format.

    Confluence uses the format: #{PageTitleWithoutSpaces}-{HeaderTextPascalCase}

    Args:
        markdown_anchor: The markdown anchor (e.g., "architecture-overview")
        page_title: The Confluence page title (e.g., "Foundations for Internet Publishing")

    Returns:
        Confluence-formatted anchor (e.g., "FoundationsforInternetPublishing-ArchitectureOverview")

    """
    # Remove spaces from page title
    page_title_no_spaces = page_title.replace(" ", "")

    # Convert markdown anchor to PascalCase
    # Split on hyphens, capitalize first letter of each word, remove hyphens
    if markdown_anchor:
        words = markdown_anchor.split("-")
        header_pascal_case = "".join(word.capitalize() for word in words if word)
        return f"{page_title_no_spaces}-{header_pascal_case}"

    return page_title_no_spaces


class RelativeLink(NamedTuple):
    path: str
    fragment: str
    replacement: str
    original: str
    escaped_original: str


class ConfluenceTag:
    def __init__(self, name, text="", attrib=None, namespace="ac", cdata=False):
        self.name = name
        self.text = text
        self.namespace = namespace
        if attrib is None:
            attrib = {}
        self.attrib = attrib
        self.children = []
        self.cdata = cdata

    def render(self):
        namespaced_name = self.add_namespace(self.name, namespace=self.namespace)
        namespaced_attribs = {
            self.add_namespace(
                attribute_name, namespace=self.namespace
            ): attribute_value
            for attribute_name, attribute_value in self.attrib.items()
        }

        content = "<{}{}>{}{}</{}>".format(
            namespaced_name,
            " {}".format(
                " ".join(
                    [
                        f'{name}="{value}"'
                        for name, value in sorted(namespaced_attribs.items())
                    ]
                )
            )
            if namespaced_attribs
            else "",
            "".join([child.render() for child in self.children]),
            f"<![CDATA[{self.text}]]>" if self.cdata else self.text,
            namespaced_name,
        )
        return f"{content}\n"

    @staticmethod
    def add_namespace(tag, namespace):
        return f"{namespace}:{tag}"

    def append(self, child):
        self.children.append(child)


class ConfluenceRenderer(mistune.HTMLRenderer):
    def __init__(
        self,
        strip_header=False,
        remove_text_newlines=False,
        enable_relative_links=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.strip_header = strip_header
        self.remove_text_newlines = remove_text_newlines
        self.attachments = list()
        self.title = None
        self.enable_relative_links = enable_relative_links
        self.relative_links: List[RelativeLink] = list()

    def reinit(self):
        self.attachments = list()
        self.relative_links = list()
        self.title = None

    def header(self, text, level, raw=None):
        if self.title is None and level == 1:
            self.title = text
            # Don't duplicate page title as a header
            if self.strip_header:
                return ""

        return super(ConfluenceRenderer, self).header(text, level, raw=raw)

    def structured_macro(self, name, text=""):
        return ConfluenceTag("structured-macro", attrib={"name": name}, text=text)

    def parameter(self, name, value):
        parameter_tag = ConfluenceTag("parameter", attrib={"name": name})
        parameter_tag.text = value
        return parameter_tag

    def plain_text_body(self, text):
        body_tag = ConfluenceTag("plain-text-body", cdata=True)
        body_tag.text = text
        return body_tag

    def rich_text_body(self, text):
        body_tag = ConfluenceTag("rich-text-body", cdata=False)
        body_tag.text = text
        return body_tag

    def link(self, text, url, title=None):
        parsed_link = urlparse(url)
        if (
            self.enable_relative_links
            and (not parsed_link.scheme and not parsed_link.netloc)
            and parsed_link.path
        ):
            # relative link
            replacement_link = f"md2cf-internal-link-{uuid.uuid4()}"
            self.relative_links.append(
                RelativeLink(
                    # make sure to unquote the url as relative paths
                    # might have escape sequences
                    path=unquote(parsed_link.path),
                    replacement=replacement_link,
                    fragment=parsed_link.fragment,
                    original=url,
                    escaped_original=mistune.escape_link(url),
                )
            )
            url = replacement_link
        return super(ConfluenceRenderer, self).link(text, url, title)

    def text(self, text):
        if self.remove_text_newlines:
            text = text.replace("\n", " ")

        return super().text(text)

    def block_code(self, code, info=None):
        root_element = self.structured_macro("code")
        if info is not None:
            lang_parameter = self.parameter(name="language", value=info)
            root_element.append(lang_parameter)
        root_element.append(self.parameter(name="linenumbers", value="true"))
        root_element.append(self.plain_text_body(code))
        return root_element.render()

    def image(self, alt, url, title=None, width=None, height=None):
        attributes = {"alt": alt,
                      "title": title if title is not None else alt,
                     }
        if width:
            attributes["width"] = width
        if height:
            attributes["height"] = height

        root_element = ConfluenceTag(name="image", attrib=attributes)
        parsed_source = urlparse(url)
        if not parsed_source.netloc:
            # Local file, requires upload
            basename = Path(url).name
            url_tag = ConfluenceTag(
                "attachment", attrib={"filename": basename}, namespace="ri"
            )
            self.attachments.append(url)
        else:
            url_tag = ConfluenceTag("url", attrib={"value": url}, namespace="ri")
        root_element.append(url_tag)

        return root_element.render()

    def strikethrough(self, text):
        return f"""<span style="text-decoration: line-through;">{text}</span>"""

    def task_list_item(self, text, checked=False, **attrs):
        return f"""
               <ac:task-list>
               <ac:task>
                   <ac:task-status>{"in" if not checked else ""}complete</ac:task-status>
                   <ac:task-body>{text}</ac:task-body>
               </ac:task>
               </ac:task-list>
               """

    def block_spoiler(self, text):
        lines = text.splitlines(keepends=True)
        firstline = re.sub('<.*?>', '', lines[0])

        root_element = self.structured_macro("expand")
        title_param = self.parameter(name="title", value=firstline)
        root_element.append(title_param)

        root_element.append(self.rich_text_body(''.join(lines[1:])))
        return root_element.render()


    def mark(self, text):
        return f"""<span style="background: yellow;">{text}</span>"""

    def insert(self, text):
        return f"""<span style="color: red;">{text}</span>"""

    def admonition(self, text: str, name: str, **attrs) -> str:
        confluence_mapping = {"tip" : "tip",
                              "attention": "warning",
                              "caution": "warning",
                              "danger": "warning",
                              "error": "warning",
                              "hint" : "tip",
                              "important": "note",
                              "note": "info",
                              "warning": "warning"}

        adm_class = confluence_mapping.get(name, "info")
        root_element = self.structured_macro(name=adm_class, text=text)
        return root_element.render()

    def admonition_title(self, text: str) -> str:
        param = self.parameter(name="title", value=text)
        return param.render()


    def admonition_content(self, text: str) -> str:
        body = self.rich_text_body(text)
        return body.render()

    def block_image(
        self,
        src: str,
        alt: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        **attrs: Any,
    ) -> str:
        return self.image(alt, src, alt, width, height)
