"""Tests for scripts/generate_readme.py markdown analysis and README generation."""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_readme import (
    extract_content_after_frontmatter,
    extract_from_docs,
    extract_section,
    load_mapping_config,
    process_section_mapping,
)


class TestExtractContentAfterFrontmatter:
    """Test frontmatter removal from markdown content."""

    def test_removes_yaml_frontmatter(self) -> None:
        """Content with YAML frontmatter should have it removed."""
        content = dedent("""
            ---
            title: Test Page
            author: Test Author
            ---

            # Main Content

            This is the actual content.
            """).strip()

        result = extract_content_after_frontmatter(content)

        assert result == dedent("""
            # Main Content

            This is the actual content.
            """).strip()

    def test_returns_unchanged_without_frontmatter(self) -> None:
        """Content without frontmatter should be returned unchanged."""
        content = dedent("""
            # Main Content

            This is the actual content.
            """).strip()

        result = extract_content_after_frontmatter(content)

        assert result == content

    def test_handles_empty_content(self) -> None:
        """Empty content should be returned as-is."""
        result = extract_content_after_frontmatter("")
        assert result == ""

    def test_handles_only_frontmatter(self) -> None:
        """Content with only frontmatter should return empty string."""
        content = dedent("""
            ---
            title: Test
            ---
            """).strip()

        result = extract_content_after_frontmatter(content)
        assert result == ""


class TestExtractSection:
    """Test section extraction from markdown content."""

    def test_extracts_level_2_section(self) -> None:
        """Should extract content under a level 2 header."""
        content = dedent("""
            # Title

            ## Section One

            Content of section one.

            ## Section Two

            Content of section two.
            """).strip()

        result = extract_section(content, "Section One", level=2)

        assert result == "Content of section one."

    def test_extracts_level_3_section(self) -> None:
        """Should extract content under a level 3 header."""
        content = dedent("""
            ## Parent

            ### Subsection

            Subsection content here.

            ### Another Subsection

            More content.
            """).strip()

        result = extract_section(content, "Subsection", level=3)

        assert result == "Subsection content here."

    def test_returns_empty_for_nonexistent_section(self) -> None:
        """Should return empty string for section that doesn't exist."""
        content = dedent("""
            ## Section One

            Content here.
            """).strip()

        result = extract_section(content, "Nonexistent Section", level=2)

        assert result == ""

    def test_extracts_until_same_level_header(self) -> None:
        """Should stop extraction at next same-level header."""
        content = dedent("""
            ## Section One

            Line 1.
            Line 2.

            ### Subsection

            Subsection content.

            ## Section Two

            Should not be included.
            """).strip()

        result = extract_section(content, "Section One", level=2)

        expected = dedent("""
            Line 1.
            Line 2.

            ### Subsection

            Subsection content.
            """).strip()

        assert result == expected

    def test_extracts_until_higher_level_header(self) -> None:
        """Should stop extraction at higher-level header."""
        content = dedent("""
            ## Section One

            Content here.

            # Main Title

            Should not be included.
            """).strip()

        result = extract_section(content, "Section One", level=2)

        assert result == "Content here."


class TestProcessSectionMapping:
    """Test processing of individual section mappings."""

    def test_processes_full_file_without_section(self, tmp_path: Path) -> None:
        """Should extract entire file content when no section specified."""
        test_file = tmp_path / "test.md"
        test_file.write_text(dedent("""
            ---
            title: Test
            ---

            # Content

            All of this content.
            """).strip())

        mapping = {"file": str(test_file)}
        result = process_section_mapping(mapping, tmp_path.parent)

        assert "# Content" in result
        assert "All of this content." in result
        assert "title: Test" not in result

    def test_processes_specific_section(self, tmp_path: Path) -> None:
        """Should extract specific section when specified."""
        test_file = tmp_path / "test.md"
        test_file.write_text(dedent("""
            ## Section A

            Content A.

            ## Section B

            Content B.
            """).strip())

        mapping = {"file": str(test_file), "section": "Section B", "level": 2}
        result = process_section_mapping(mapping, tmp_path.parent)

        assert result == "Content B."

    def test_adds_prefix_when_specified(self, tmp_path: Path) -> None:
        """Should add prefix to extracted content."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Content here.")

        mapping = {"file": str(test_file), "prefix": "### Title\n\n"}
        result = process_section_mapping(mapping, tmp_path.parent)

        assert result == "### Title\n\nContent here."

    def test_adds_suffix_when_specified(self, tmp_path: Path) -> None:
        """Should add suffix to extracted content."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Content here.")

        mapping = {"file": str(test_file), "suffix": "\n\nExtra text."}
        result = process_section_mapping(mapping, tmp_path.parent)

        assert result == "Content here.\n\nExtra text."

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """Should return empty string for non-existent file."""
        mapping = {"file": "nonexistent.md"}
        result = process_section_mapping(mapping, tmp_path)

        assert result == ""


class TestLoadMappingConfig:
    """Test loading of YAML mapping configuration."""

    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        """Should load valid YAML configuration."""
        config_file = tmp_path / "mapping.yaml"
        config_file.write_text(dedent("""
            section1:
              file: docs/file1.md
              section: Header
              level: 2

            section2:
              file: docs/file2.md
            """).strip())

        result = load_mapping_config(config_file)

        assert "section1" in result
        assert "section2" in result
        assert result["section1"]["file"] == "docs/file1.md"
        assert result["section1"]["section"] == "Header"

    def test_loads_list_mappings(self, tmp_path: Path) -> None:
        """Should handle list of mappings for a section."""
        config_file = tmp_path / "mapping.yaml"
        config_file.write_text(dedent("""
            combined:
              - file: docs/file1.md
                section: Part 1
              - file: docs/file2.md
                section: Part 2
            """).strip())

        result = load_mapping_config(config_file)

        assert "combined" in result
        assert isinstance(result["combined"], list)
        assert len(result["combined"]) == 2


class TestExtractFromDocs:
    """Test extraction of multiple sections from documentation."""

    def test_extracts_single_sections(self, tmp_path: Path) -> None:
        """Should extract multiple single-file sections."""
        # Create test files
        file1 = tmp_path / "file1.md"
        file1.write_text("## Header\n\nContent 1.")

        file2 = tmp_path / "file2.md"
        file2.write_text("## Header\n\nContent 2.")

        mapping_config = {
            "section1": {"file": str(file1), "section": "Header", "level": 2},
            "section2": {"file": str(file2), "section": "Header", "level": 2},
        }

        result = extract_from_docs(mapping_config, tmp_path.parent)

        assert result["section1"] == "Content 1."
        assert result["section2"] == "Content 2."

    def test_combines_multiple_sources(self, tmp_path: Path) -> None:
        """Should combine multiple sources into one section."""
        file1 = tmp_path / "file1.md"
        file1.write_text("Content A.")

        file2 = tmp_path / "file2.md"
        file2.write_text("Content B.")

        mapping_config = {
            "combined": [
                {"file": str(file1)},
                {"file": str(file2)},
            ]
        }

        result = extract_from_docs(mapping_config, tmp_path.parent)

        assert result["combined"] == "Content A.\nContent B."

    def test_handles_empty_extractions(self, tmp_path: Path) -> None:
        """Should handle sections with no content extracted."""
        file1 = tmp_path / "file1.md"
        file1.write_text("## Wrong Header\n\nContent.")

        mapping_config = {
            "section1": {"file": str(file1), "section": "Missing Header", "level": 2}
        }

        result = extract_from_docs(mapping_config, tmp_path.parent)

        assert result["section1"] == ""
