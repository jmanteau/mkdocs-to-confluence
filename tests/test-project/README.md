# Test Project for mkdocs-to-confluence

This is an isolated test environment for the mkdocs-to-confluence plugin.

## Structure

- `mkdocs.yml` - MkDocs configuration with the plugin enabled in dry-run mode
- `pyproject.toml` - Isolated dependencies (mkdocs, mkdocs-material)
- `../docs-test/` - Test documentation source files (shared)

## Usage

From the project root, run:

```bash
make test-dryrun
```

This will:
1. Set up the isolated environment with uv
2. Install the plugin from the parent directory in editable mode
3. Build the test docs with dry-run export enabled
4. Export all pages to `confluence-export/`

## Manual Testing

You can also run manually:

```bash
cd tests/test-project
uv sync
uv pip install -e ../..
uv run mkdocs build
```

The exported pages will be in `confluence-export/`.
