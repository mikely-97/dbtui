# Changelog

## [0.4.0] - 2026-03-22

### Added
- DAG keyboard navigation — arrow keys + Enter to jump to related models
- CTE-aware column lineage — correctly handles WITH clauses and JOINs
- Run panel output history — ← Prev / Next → between past runs
- dbt test results inline — Tests tab with per-test pass/fail DataTable
- Schema.yml editor modal — edit description/tags with `e` key
- Model search by tag and materialization type filters
- Keyboard shortcut help screen — `?` key
- `{{ source() }}` support — parse, graph, and lineage
- Recently visited models screen — `g` key
- dbt compile preview tab — show compiled SQL
- Mermaid DAG export — `m` key saves `.mmd` file
- Bookmark/favorite models — `b` to toggle, `B` to view
- GitHub Actions CI (lint + test) and PyPI publish workflow

### Changed
- Split property_discovery.py (716 lines) into focused discovery sub-modules
- Extracted properties_panel formatting into properties_formatter.py
- Consolidated errors.py + exceptions.py into single module
- Removed redundant _cached wrapper functions
- Added ruff linter configuration, fixed 179 lint issues
- Centralized test fixtures into conftest.py
- Added proper __init__.py exports for all frontend packages

### Fixed
- Bare except clause in property_discovery.py → except Exception
- Inconsistent logging in property_claim.py — now uses get_logger()
- Wildcard import in common/__init__.py → explicit imports

## [0.3.0] - 2026-03-21

### Added
- Fuzzy model search with tiered scoring (SequenceMatcher)
- Entity type filters in model search (Models / Macros checkboxes)
- Path prefix filter in model search
- ASCII DAG visualisation screen (`d` key) with adjustable depth
- Full-screen property viewer (`v` key) with live filter
- Documentation tab in model view (Markdown rendering)
- Git integration tab in model view (status bar, commit log, blame view)
- Run/Test/Build panel in model view with streaming output (`r`/`t` keys)
- Column-level lineage screen (`l` key) via sqlglot
- Multi-project workspace support with tab bar
- Macro test suite and fixtures
- WorkspaceEntry persistence in cache

## [0.2.1] - earlier
- Initial release
