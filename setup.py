"""Setup configuration for mkdocs-to-confluence."""

from setuptools import find_packages, setup

setup(
    name="mkdocs-to-confluence",
    version="0.2.0",
    description="MkDocs plugin for converting and uploading Markdown pages to Confluence (via REST API)",
    keywords="mkdocs markdown confluence documentation",
    url="https://github.com/jmanteau/mkdocs-to-confluence/",
    author="Julien Manteau",
    author_email="jmanteau@gmail.com",
    license="MIT",
    python_requires=">=3.8",
    install_requires=["mkdocs>=1.1", "jinja2", "mistune>=3.1.2", "mime>=0.1.0", "requests"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={"mkdocs.plugins": ["mkdocs-to-confluence = mkdocs_to_confluence.plugin:MkdocsWithConfluence"]},
)
