"""Navigation structure test fixtures."""

# Simple flat navigation
SIMPLE_NAV_REPR = """Page(title='Home', url='index.html')
Page(title='Getting Started', url='getting-started/')"""

# Nested navigation with sections
NESTED_NAV_REPR = """Section(title='User Guide')
  Page(title='Installation', url='user-guide/installation/')
  Page(title='Configuration', url='user-guide/configuration/')
Section(title='API Reference')
  Page(title='Core API', url='api/core/')"""

# Navigation with multiple indent levels
DEEP_NAV_REPR = """Section(title='Documentation')
  Section(title='Tutorials')
    Page(title='Quick Start', url='docs/tutorials/quick-start/')
    Page(title='Advanced Topics', url='docs/tutorials/advanced/')
  Section(title='Reference')
    Page(title='API', url='docs/reference/api/')"""

# Page without title in nav (URL only)
PAGE_NO_TITLE = "Page(title=None, url='index/')"

# Section without title
SECTION_NO_TITLE = "Section(title=None, url='guides/')"

# Expected tab_nav outputs
EXPECTED_SIMPLE_TAB_NAV = [
    "Home",
    "Getting Started",
]

EXPECTED_NESTED_TAB_NAV = [
    "User Guide",
    "  Installation",
    "  Configuration",
    "API Reference",
    "  Core API",
]

EXPECTED_DEEP_TAB_NAV = [
    "Documentation",
    "  Tutorials",
    "    Quick Start",
    "    Advanced Topics",
    "  Reference",
    "    API",
]
