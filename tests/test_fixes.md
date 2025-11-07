# Test Fixes Needed

## Issue 1: dryrun not initialized
- `dryrun` only set in `on_config()`, not `__init__`
- Need to initialize or call `on_config` properly

## Issue 2: Regex mismatch for file:// images
- Pattern expects space+s after closing quote but fixture doesn't have it

## Issue 3: Code doesn't handle empty results
- `find_page_version` and `find_parent_name` crash on empty results
- Need defensive checks

## Issue 4: Section title parsing
- Regex expects specific format that test doesn't provide
