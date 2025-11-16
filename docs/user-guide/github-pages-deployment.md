---
title: GitHub Pages Deployment
---

# Deploy Documentation to GitHub Pages

Set up automatic documentation deployment to GitHub Pages using GitHub Actions.

## Prerequisites

- Repository hosted on GitHub
- Write access to repository settings

## Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Build and deployment**:
   - **Source**: Select "GitHub Actions"

That's it! No need to select a branch or folder.

## Step 2: Verify Workflow File

The repository includes `.github/workflows/docs.yml` which:

- Triggers on pushes to `main` branch (when docs files change)
- Can be manually triggered via workflow_dispatch
- Uses Makefile targets for consistency:
  - `make py-setup` - Install dependencies
  - `make docs-build-strict` - Build docs (fails on warnings)

## Step 3: Push to Main Branch

```bash
git add .github/workflows/docs.yml
git commit -m "Add GitHub Pages deployment workflow"
git push origin main
```

## Step 4: Monitor Deployment

1. Go to **Actions** tab in your repository
2. Watch the "Deploy Documentation" workflow run
3. Once complete, your docs are live!

## Accessing Your Documentation

Your documentation will be available at:

```
https://<username>.github.io/<repository>/
```

For example:
```
https://jmanteau.github.io/mkdocs-to-confluence/
```

## Workflow Details

### Trigger Conditions

The workflow runs when:

- Files in `docs/` change
- `mkdocs.yml` is modified
- `README.md.j2` or `scripts/generate_readme.py` change
- Workflow file itself is modified
- Manually triggered

### Build Process

```yaml
jobs:
  build:
    - Install Python 3.12
    - Install uv
    - Install dependencies (make py-setup)
    - Build docs in strict mode (make docs-build-strict)
    - Upload site artifact

  deploy:
    - Deploy to GitHub Pages
```

### Strict Mode

The workflow uses `make docs-build-strict` which:

- Fails build on warnings
- Catches broken links
- Ensures documentation quality
- Validates all references

## Troubleshooting

### Build Fails on Warnings

The workflow uses strict mode. Fix all warnings before merging:

```bash
# Test locally
make docs-build-strict
```

Common warnings:
- Broken internal links
- Missing images
- Unrecognized relative links

### Permissions Error

If deployment fails with permissions error:

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions":
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"
3. Save changes

### Custom Domain

To use a custom domain:

1. Go to **Settings** → **Pages**
2. Enter your custom domain under "Custom domain"
3. Add a `CNAME` file to your `docs/` directory:
   ```
   docs.example.com
   ```

## Advanced: Versioned Documentation

The Makefile includes `make docs-deploy` which uses [mike](https://github.com/jimporter/mike) for versioned docs:

```bash
make docs-deploy
```

This creates version tags like:
- `https://example.github.io/project/0.5.0/`
- `https://example.github.io/project/latest/` (alias)

To use versioned docs in CI:

1. Generate a deploy key or use `GITHUB_TOKEN`
2. Update workflow to use `make docs-deploy`
3. Configure mike version strategy

## Manual Deployment

To deploy manually:

```bash
# Build docs
make docs-build-strict

# Deploy using gh-pages branch (if not using Actions)
uv run mkdocs gh-deploy
```

## Local Testing

Test the deployment process locally:

```bash
# Build docs
make docs-build-strict

# Serve built site
cd site
python -m http.server 8000
```

Open http://localhost:8000 to preview.

## Workflow Configuration

The workflow file at `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
      - 'README.md.j2'
      - 'scripts/generate_readme.py'
      - '.github/workflows/docs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: make py-setup
      - run: make docs-build-strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

## Next Steps

- [Basic Usage](../user-guide/basic-usage.md) - Publishing workflow
- [Contributing](../contributing.md) - How to contribute to docs
- [Configuration Reference](../reference/configuration.md) - MkDocs config
