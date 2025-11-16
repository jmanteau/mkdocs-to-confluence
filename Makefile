# mkdocs-with-confluence Makefile
# Modern Python project automation using uv

.DEFAULT_GOAL := help

# Load environment variables from .env file if it exists
-include .env
export
.PHONY: help py-setup py-clean py-ruff py-ruff-fix py-mypy py-test py-report test-dryrun py-security py-complexity py-pre-commit py-ci \
        clean lint-fix tests complexity quality info run \
        docs-serve docs-build docs-deploy adr-new adr-list \
        build test-upload upload release test-install publish-check \
        git-status git-commit git-tag deploy-production version

# Colors for help output
RESET := \033[0m
BOLD := \033[1m
CYAN := \033[36m
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m

##@ Help
help: ## Display this help message
	@echo "$(BLUE)mkdocs-with-confluence$(RESET)"
	@echo "=================================="
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# Utility functions
cmd-exists-%:
	@hash $(*) > /dev/null 2>&1 || \
		(echo "ERROR: '$(*)' must be installed and available on your PATH."; exit 1)

guard-%:
	@if [ -z '${${*}}' ]; then echo 'ERROR: variable $* not set' && exit 1; fi

##@ Setup
py-setup: ## Setup development environment
py-setup: cmd-exists-uv
	uv --native-tls venv
	uv --native-tls sync --group dev --group docs

##@ Cleanup
py-clean: ## Clean up build artifacts and caches
py-clean:
	@echo "$(CYAN)Cleaning build artifacts and caches...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf tests/test-project/confluence-export/
	rm -rf tests/test-project/site/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "confluence_page_*.html" -delete
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

clean: py-clean ## Alias for py-clean

##@ Code Quality
py-ruff: ## Run ruff linter
py-ruff: cmd-exists-uv
	@echo "$(BLUE)Running ruff linter...$(RESET)"
	uvx ruff check .
	@echo "$(GREEN)✓ Linting complete$(RESET)"

py-ruff-fix: ## Fix ruff issues and format code
py-ruff-fix: cmd-exists-uv
	@echo "$(BLUE)Fixing linting issues and formatting...$(RESET)"
	uvx ruff check . --fix
	uvx ruff format .
	@echo "$(GREEN)✓ Code fixed and formatted$(RESET)"

lint-fix: py-ruff-fix ## Alias for py-ruff-fix

py-mypy: ## Run mypy type checker
py-mypy: cmd-exists-uv
	@echo "$(BLUE)Running mypy type checker...$(RESET)"
	uv --native-tls run mypy mkdocs_with_confluence tests
	@echo "$(GREEN)✓ Type checking complete$(RESET)"

py-security: ## Run security audit
py-security: cmd-exists-uv
	@echo "$(BLUE)Running security audit...$(RESET)"
	@echo "$(YELLOW)Checking dependencies with pip-audit...$(RESET)"
	-uv --native-tls run pip-audit
	@echo ""
	@echo "$(YELLOW)Scanning code with bandit...$(RESET)"
	uv --native-tls run bandit -r mkdocs_with_confluence
	@echo "$(GREEN)✓ Security audit complete$(RESET)"

py-complexity: ## Run complexity analysis
py-complexity: cmd-exists-uv
	@echo "$(BLUE)Running complexity analysis...$(RESET)"
	@echo "$(YELLOW)Cyclomatic Complexity:$(RESET)"
	@uv --native-tls run radon cc --min B --max F --show-complexity --average mkdocs_with_confluence
	@echo ""
	@echo "$(YELLOW)Maintainability Index:$(RESET)"
	@uv --native-tls run radon mi --min B --max F --show mkdocs_with_confluence
	@echo ""
	@echo "$(YELLOW)Raw Metrics:$(RESET)"
	@uv --native-tls run radon raw --summary mkdocs_with_confluence
	@echo "$(GREEN)✓ Complexity analysis complete$(RESET)"

complexity: py-complexity ## Alias for py-complexity

quality: py-ruff py-mypy py-security ## Run all quality checks (lint, type check, security)
	@echo "$(GREEN)✓ All quality checks passed$(RESET)"

##@ Testing
py-test: ## Run pytest
py-test: cmd-exists-uv
	@echo "$(BLUE)Running tests...$(RESET)"
	uv --native-tls run pytest
	@echo "$(GREEN)✓ Tests complete$(RESET)"

tests: py-test ## Alias for py-test

py-report: ## Generate coverage report
py-report: cmd-exists-uv
	uv --native-tls run coverage html
	@echo "Coverage report: file://$(PWD)/htmlcov/index.html"

test-dryrun: ## Test dry-run export with sample docs
test-dryrun: cmd-exists-uv
	@echo "$(BLUE)Testing dry-run export functionality...$(RESET)"
	@echo "$(YELLOW)Setting up test environment...$(RESET)"
	@cd tests/test-project && uv --native-tls sync
	@echo "$(CYAN)Installing plugin from local source...$(RESET)"
	@cd tests/test-project && uv --native-tls pip install -e ../..
	@echo "$(YELLOW)Cleaning previous export and temp files...$(RESET)"
	@rm -rf tests/test-project/confluence-export tests/test-project/site
	@rm -f tests/test-project/confluence_page_*.html
	@echo "$(CYAN)Building docs with dry-run mode...$(RESET)"
	@cd tests/test-project && uv --native-tls run mkdocs build
	@echo ""
	@echo "$(GREEN)✓ Dry-run export complete$(RESET)"
	@echo "$(CYAN)Export location: tests/test-project/confluence-export/$(RESET)"
	@echo ""
	@echo "$(YELLOW)Exported structure:$(RESET)"
	@tree tests/test-project/confluence-export/ -L 2 2>/dev/null || find tests/test-project/confluence-export -type f | head -20
	@echo ""
	@echo "$(YELLOW)Total pages exported:$(RESET)"
	@find tests/test-project/confluence-export -name "page.html" | wc -l | awk '{print "  " $$1 " pages"}'

##@ Development
py-pre-commit: ## Install prek hooks
py-pre-commit: cmd-exists-uv
	uvx --native-tls prek install

githooks-setup: py-pre-commit ## Install git hooks (alias for py-pre-commit)

githooks: ## Run prek hooks manually on all files
githooks: cmd-exists-uv
	@echo "$(BLUE)Running prek hooks on all files...$(RESET)"
	uvx --native-tls prek run --all-files
	@echo "$(GREEN)✓ Git hooks passed$(RESET)"

py-ci: py-ruff py-mypy py-test py-security py-complexity ## Run all CI checks
	@echo "$(GREEN)✓ All CI checks passed$(RESET)"

##@ Documentation
readme: ## Generate README.md from template and docs
readme: cmd-exists-uv
	@echo "$(BLUE)Generating README.md...$(RESET)"
	uv --native-tls run python scripts/generate_readme.py
	@echo "$(GREEN)✓ README.md generated$(RESET)"

docs-serve: ## Serve documentation locally (with live reload)
docs-serve: cmd-exists-uv
	uv --native-tls run mkdocs serve -a 0.0.0.0:8000

serve: docs-serve

docs-build: readme ## Build documentation (includes README generation)
docs-build: cmd-exists-uv
	@echo "$(BLUE)Building documentation...$(RESET)"
	uv --native-tls run mkdocs build
	@echo "$(GREEN)✓ Documentation built$(RESET)"

docs-build-strict: readme ## Build documentation in strict mode (fails on warnings)
docs-build-strict: cmd-exists-uv
	@echo "$(BLUE)Building documentation (strict mode)...$(RESET)"
	uv --native-tls run mkdocs build --strict
	@echo "$(GREEN)✓ Documentation built$(RESET)"

docs: docs-build ## Alias for docs-build (generate README + build docs)

docs-deploy: readme ## Deploy documentation with version from package
docs-deploy: cmd-exists-uv
	@echo "$(BLUE)Getting package version...$(RESET)"
	@VERSION=$$(grep '^version =' pyproject.toml | cut -d'"' -f2); \
	echo "$(YELLOW)Deploying docs for version: $$VERSION$(RESET)"; \
	echo "$(BLUE)Building documentation...$(RESET)"; \
	uv --native-tls run mkdocs build; \
	echo "$(CYAN)Deploying to GitHub Pages...$(RESET)"; \
	uv --native-tls run mike deploy --push --update-aliases $$VERSION latest; \
	uv --native-tls run mike set-default --push latest
	@echo "$(GREEN)✓ Documentation deployed$(RESET)"

##@ Architecture Decision Records (ADR)
adr-new: ## Create a new Architecture Decision Record (use: make adr-new TITLE="your title")
adr-new: guard-TITLE
	@echo "$(CYAN)Creating new ADR: $(TITLE)$(RESET)"
	@NEXT_NUM=$$(ls docs/adr/[0-9][0-9][0-9]-*.md 2>/dev/null | wc -l | awk '{printf "%03d", $$1 + 1}'); \
	FILENAME="docs/adr/$${NEXT_NUM}-$$(echo "$(TITLE)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$$//g').md"; \
	cp docs/adr/template.md "$$FILENAME"; \
	sed -i.bak "s/ADR-XXX/ADR-$${NEXT_NUM}/g" "$$FILENAME"; \
	sed -i.bak "s/\[Short descriptive title\]/$(TITLE)/g" "$$FILENAME"; \
	rm "$${FILENAME}.bak"; \
	echo "Created: $$FILENAME"

adr-list: ## List all Architecture Decision Records
adr-list:
	@echo "$(CYAN)Architecture Decision Records:$(RESET)"
	@ls -1 docs/adr/[0-9][0-9][0-9]-*.md 2>/dev/null | sed 's|docs/adr/||' | sed 's|\.md$$||' || echo "No ADRs found"

##@ Utilities
run: ## Run the simple main.py application
run: cmd-exists-uv
	uv --native-tls run python -m mkdocs_with_confluence.main

run-cli: ## Run the Cyclopts CLI with --help
run-cli: cmd-exists-uv
	uv --native-tls run mkdocs-with-confluence --help

info: ## Show project information
info:
	@echo "$(BLUE)mkdocs-with-confluence$(RESET)"
	@echo "=================================="
	@echo ""
	@echo "$(YELLOW)Python & Tools:$(RESET)"
	@printf "  uv: " && uv --version 2>/dev/null || echo "Not found"
	@printf "  python: " && uv --native-tls run python --version 2>/dev/null || echo "Not found"
	@echo ""
	@echo "$(YELLOW)Key Dependencies:$(RESET)"
	@printf "  ruff: " && uvx --native-tls ruff --version 2>/dev/null | head -n1 || echo "Not installed"
	@printf "  mypy: " && uv --native-tls run mypy --version 2>/dev/null || echo "Not installed"
	@printf "  pytest: " && uv --native-tls run pytest --version 2>/dev/null | head -n1 || echo "Not installed"
	@echo ""
	@echo "$(YELLOW)Project Structure:$(RESET)"
	@echo "  Source: src/"
	@echo "  Tests: tests/"
	@echo "  Docs: docs/"
	@echo ""

##@ Publishing
publish-check: ## Check if ready to publish (version, changelog, tests)
publish-check: cmd-exists-uv
	@echo "$(BLUE)Checking publish readiness...$(RESET)"
	@echo "$(YELLOW)Version in setup.py:$(RESET)"
	@grep 'version=' setup.py | head -n1
	@echo "$(YELLOW)Version in pyproject.toml:$(RESET)"
	@grep '^version =' pyproject.toml
	@echo "$(YELLOW)Latest CHANGELOG entry:$(RESET)"
	@grep -A1 '^\[' CHANGELOG.md | head -n2
	@echo ""
	@echo "$(CYAN)Running tests before build...$(RESET)"
	@uv --native-tls run pytest -q
	@echo "$(GREEN)✓ Ready to publish$(RESET)"

build: py-clean ## Build distribution packages (wheel and source)
build: cmd-exists-uv
	@echo "$(BLUE)Building distribution packages...$(RESET)"
	@echo "$(CYAN)Installing build tool...$(RESET)"
	uv --native-tls pip install --upgrade build
	@echo "$(CYAN)Building distributions...$(RESET)"
	uv --native-tls run python -m build
	@echo "$(GREEN)✓ Build complete$(RESET)"
	@echo "$(YELLOW)Distribution files:$(RESET)"
	@ls -lh dist/

test-upload: build ## Upload to TestPyPI (requires credentials)
test-upload: cmd-exists-uv
	@echo "$(BLUE)Uploading to TestPyPI...$(RESET)"
	@echo "$(YELLOW)Note: You'll need TestPyPI credentials$(RESET)"
	@echo "$(YELLOW)Username: __token__$(RESET)"
	@echo "$(YELLOW)Password: Your TestPyPI API token$(RESET)"
	uv --native-tls pip install --upgrade twine
	uv --native-tls run python -m twine upload --verbose --repository testpypi dist/*
	@echo "$(GREEN)✓ Upload to TestPyPI complete$(RESET)"
	@echo "$(CYAN)Test installation with:$(RESET)"
	@echo "  make test-install"

test-install: ## Test installation from TestPyPI
	@echo "$(BLUE)Testing installation from TestPyPI...$(RESET)"
	@echo "$(YELLOW)Creating test environment...$(RESET)"
	@rm -rf /tmp/test-mkdocs-to-confluence-env
	python3 -m venv /tmp/test-mkdocs-to-confluence-env
	@echo "$(CYAN)Installing from TestPyPI (with dependencies from PyPI)...$(RESET)"
	/tmp/test-mkdocs-to-confluence-env/bin/pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mkdocs-to-confluence
	@echo "$(CYAN)Testing import...$(RESET)"
	/tmp/test-mkdocs-to-confluence-env/bin/python -c "from mkdocs_to_confluence.plugin import MkdocsWithConfluence; print('✓ Import successful')"
	@echo "$(CYAN)Testing exporter import...$(RESET)"
	/tmp/test-mkdocs-to-confluence-env/bin/python -c "from mkdocs_to_confluence.exporter import ConfluenceExporter; print('✓ Exporter import successful')"
	@echo "$(GREEN)✓ TestPyPI installation verified$(RESET)"
	@rm -rf /tmp/test-mkdocs-to-confluence-env

upload: build ## Upload to production PyPI (requires credentials)
upload: cmd-exists-uv
	@echo "$(BOLD)$(YELLOW)⚠️  WARNING: Uploading to PRODUCTION PyPI$(RESET)"
	@echo "$(YELLOW)This action cannot be undone!$(RESET)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "$(RED)Upload cancelled$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Uploading to PyPI...$(RESET)"
	@echo "$(YELLOW)Username: __token__$(RESET)"
	@echo "$(YELLOW)Password: Your PyPI API token$(RESET)"
	uv --native-tls pip install --upgrade twine
	uv --native-tls run python -m twine upload dist/*
	@echo "$(GREEN)✓ Upload to PyPI complete$(RESET)"
	@echo "$(CYAN)Verify at: https://pypi.org/project/mkdocs-to-confluence/$(RESET)"

release: ## Interactive release workflow with version management
	@echo "$(BLUE)=====================================$(RESET)"
	@echo "$(BOLD)$(BLUE)    Release Preparation$(RESET)"
	@echo "$(BLUE)=====================================$(RESET)"
	@echo ""
	@CURRENT_VERSION=$$(grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	CHANGELOG_VERSION=$$(grep -m1 '^\[' CHANGELOG.md | sed 's/\[\([^]]*\)\].*/\1/'); \
	echo "$(CYAN)Current version in pyproject.toml:$(RESET) $$CURRENT_VERSION"; \
	echo "$(CYAN)Latest version in CHANGELOG.md:$(RESET)   $$CHANGELOG_VERSION"; \
	echo ""; \
	if [ "$$CURRENT_VERSION" != "$$CHANGELOG_VERSION" ]; then \
		echo "$(YELLOW)⚠️  WARNING: Version mismatch detected!$(RESET)"; \
		echo ""; \
	fi; \
	read -p "Do you want to create a new release? (yes/no): " do_release; \
	if [ "$$do_release" != "yes" ]; then \
		echo "$(YELLOW)Release cancelled$(RESET)"; \
		exit 0; \
	fi; \
	echo ""; \
	read -p "Enter new version (current: $$CURRENT_VERSION): " NEW_VERSION; \
	if [ -z "$$NEW_VERSION" ]; then \
		echo "$(RED)Version cannot be empty$(RESET)"; \
		exit 1; \
	fi; \
	if [ "$$NEW_VERSION" = "$$CURRENT_VERSION" ]; then \
		echo "$(YELLOW)Using existing version: $$NEW_VERSION$(RESET)"; \
	else \
		echo "$(CYAN)Updating version to: $$NEW_VERSION$(RESET)"; \
		sed -i.bak "s/^version = \".*\"/version = \"$$NEW_VERSION\"/" pyproject.toml && rm pyproject.toml.bak; \
		sed -i.bak "s/version=\".*\"/version=\"$$NEW_VERSION\"/" setup.py && rm setup.py.bak; \
		TODAY=$$(date +%Y-%m-%d); \
		if grep -q "^\[$$NEW_VERSION\]" CHANGELOG.md; then \
			echo "$(YELLOW)Version $$NEW_VERSION already exists in CHANGELOG.md, updating date...$(RESET)"; \
			sed -i.bak "s/^\[$$NEW_VERSION\] - [0-9-]*$$/[$$NEW_VERSION] - $$TODAY/" CHANGELOG.md && rm CHANGELOG.md.bak; \
		else \
			echo "$(YELLOW)⚠️  Version $$NEW_VERSION not found in CHANGELOG.md$(RESET)"; \
			echo "$(YELLOW)Please update CHANGELOG.md manually before continuing$(RESET)"; \
			read -p "Press Enter when ready to continue..."; \
		fi; \
		sed -i.bak "s|^\[Unreleased\]:.*|[Unreleased]: https://github.com/jmanteau/mkdocs-to-confluence/compare/v$$NEW_VERSION...HEAD|" CHANGELOG.md && rm CHANGELOG.md.bak; \
		PREV_VERSION=$$(grep '^\[' CHANGELOG.md | sed -n '2p' | sed 's/\[\([^]]*\)\].*/\1/'); \
		if ! grep -q "^\[$$NEW_VERSION\]:" CHANGELOG.md; then \
			echo "[$$NEW_VERSION]: https://github.com/jmanteau/mkdocs-to-confluence/compare/v$$PREV_VERSION...v$$NEW_VERSION" | \
			awk 'NR==FNR{line=$$$$0; next} /^\[Unreleased\]:/{print; print line; next}1' - CHANGELOG.md > CHANGELOG.md.tmp && \
			mv CHANGELOG.md.tmp CHANGELOG.md; \
		fi; \
		echo "$(GREEN)✓ Version updated in pyproject.toml, setup.py, and CHANGELOG.md$(RESET)"; \
	fi; \
	echo ""; \
	echo "$(CYAN)Running publish checks...$(RESET)"; \
	$(MAKE) publish-check; \
	echo ""; \
	read -p "Build and upload to TestPyPI? (yes/no): " do_upload; \
	if [ "$$do_upload" = "yes" ]; then \
		$(MAKE) test-upload; \
		echo "$(GREEN)✓ Release workflow complete$(RESET)"; \
		echo "$(CYAN)Next steps:$(RESET)"; \
		echo "  1. Test installation: make test-install"; \
		echo "  2. Commit changes: make git-commit"; \
		echo "  3. Deploy to production: make deploy-production"; \
	else \
		echo "$(YELLOW)Upload skipped$(RESET)"; \
	fi

version: ## Display current package version
	@echo "$(CYAN)Current version:$(RESET)"
	@grep '^version =' pyproject.toml | cut -d'"' -f2

##@ Git Operations
git-status: ## Show git status and pending changes
	@echo "$(BLUE)Git status:$(RESET)"
	@git status
	@echo ""
	@echo "$(YELLOW)Modified files:$(RESET)"
	@git diff --name-status

git-commit: ## Commit release changes (version, changelog, vendored deps)
	@echo "$(BLUE)Committing release changes...$(RESET)"
	@VERSION=$$(grep '^version =' pyproject.toml | cut -d'"' -f2); \
	echo "$(YELLOW)Version: $$VERSION$(RESET)"; \
	echo ""; \
	echo "$(YELLOW)Files to commit:$(RESET)"; \
	git status --short; \
	echo ""; \
	read -p "Commit these changes? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "$(RED)Commit cancelled$(RESET)"; \
		exit 1; \
	fi; \
	echo ""; \
	read -p "Enter commit message: " message; \
	if [ -z "$$message" ]; then \
		echo "$(RED)Commit message cannot be empty$(RESET)"; \
		exit 1; \
	fi; \
	git add -A; \
	git commit -m "$$message"; \
	echo "$(GREEN)✓ Changes committed$(RESET)"

git-tag: version ## Create and push git tag for current version
	@VERSION=$$(grep '^version =' pyproject.toml | cut -d'"' -f2); \
	echo "$(BLUE)Creating git tag v$$VERSION...$(RESET)"; \
	if git rev-parse "v$$VERSION" >/dev/null 2>&1; then \
		echo "$(RED)Error: Tag v$$VERSION already exists$(RESET)"; \
		exit 1; \
	fi; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	echo "$(GREEN)✓ Tag v$$VERSION created$(RESET)"; \
	echo "$(YELLOW)Pushing tag to origin...$(RESET)"; \
	git push origin "v$$VERSION"; \
	echo "$(GREEN)✓ Tag pushed to remote$(RESET)"

deploy-production: upload git-tag ## Complete production deployment (PyPI + git tag)
	@echo "$(GREEN)✓ Production deployment complete$(RESET)"
	@VERSION=$$(grep '^version =' pyproject.toml | cut -d'"' -f2); \
	echo "$(CYAN)Package published:$(RESET)"; \
	echo "  PyPI: https://pypi.org/project/mkdocs-to-confluence/$$VERSION/"; \
	echo "  GitHub: https://github.com/jmanteau/mkdocs-to-confluence/releases/tag/v$$VERSION"
