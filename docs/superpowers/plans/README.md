# dbt-tui Implementation Plans

Execute plans in this order — each builds on the previous where noted.

## Phase 0 — Housekeeping
- `2026-03-21-00-commit-macro-work.md` — commit pending macro tests (do this first)

## Phase 1 — Independent features (any order)
- `2026-03-21-enhanced-model-search.md` — fuzzy scoring, entity-type & path filters
- `2026-03-21-dag-visualization.md` — ASCII DAG screen (`d` key)
- `2026-03-21-property-viewer.md` — full-screen property table with filter (`v` key)

## Phase 2 — Model view tabs (do docs before git; both before execution)
- `2026-03-21-documentation-viewer.md` — Docs tab in model view (adds TabbedContent)
- `2026-03-21-git-integration.md` — Git tab in model view (requires TabbedContent from docs plan)
- `2026-03-21-model-execution.md` — Run/Test/Build panel in model view

## Phase 3 — Complex features
- `2026-03-21-column-level-lineage.md` — column lineage via sqlglot (`l` key)
- `2026-03-21-multiple-project-workspace.md` — multi-project tabs

## Phase 4 — v0.3.0 batch (any order, independent)
- `2026-03-21-v0.3.0-release.md` — bump version, CHANGELOG, README (do first)
- `2026-03-21-dag-keyboard-navigation.md` — arrow-key + Enter navigation in DAG view
- `2026-03-21-column-lineage-improvements.md` — CTE-aware lineage, fix JOIN attribution
- `2026-03-21-run-panel-history.md` — ← Prev / Next → run output history
- `2026-03-21-frontend-tests-new-screens.md` — Pilot tests for DagView, LineageView, etc.
- `2026-03-21-dbt-test-results-inline.md` — Tests tab with per-test pass/fail DataTable
- `2026-03-21-schema-yml-editor.md` — Edit description/tags modal (`e` key)
- `2026-03-21-model-search-tag-materialization.md` — tag & materialization filters in search
- `2026-03-21-keyboard-shortcut-help.md` — `?` key shows all bindings

## Key bindings summary (post all features)
| Key | Action |
|-----|--------|
| `f` | Model search (with entity-type, tag, mat. filters) |
| `d` | DAG visualization + keyboard navigation |
| `v` | Property viewer (full-screen) |
| `l` | Column lineage |
| `r` | Run model (inside model view) |
| `t` | Test model (inside model view) |
| `e` | Edit schema.yml (inside model view) |
| `?` | Keyboard shortcut help |
| `+` | Add project to workspace |
