# Changelog

All notable changes to dbt-tui will be documented in this file.

## [0.2.1] - 2026-02-12

### Added
- **Centralized logging system** with `--log-level` CLI parameter (DEBUG, INFO, WARNING, ERROR)
- **`--logs-dir` option** to print logs directory path and exit
- **Options screen improvements**: proper labels, descriptions, key bindings (escape/q to close), and session info display
- **Async file writes** in edit mode to keep UI responsive
- **pytest-asyncio** support for async tests

### Changed
- Removed `DBT_TUI_TIMING` environment variable in favor of `--log-level INFO`
- Properties panel now shows compact single-line items instead of full-height rows
- Property detail modal now supports "look up & edit if possible" workflow

### Fixed
- Options screen now has working key bindings and can be closed with escape
- Async frontend tests now run properly (previously skipped)

## [0.2.0] - 2026-02-11

### Added
- Property claims system for viewing model configurations from all sources
- Model view screen with properties panel
- Property editing and adding via modal dialogs
- PropertyDiscoveryCache for 22x faster project loading
- External editor support (E key)

### Changed
- Improved performance with cached YAML parsing
- Debounced context saving
