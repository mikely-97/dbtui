# Property Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated full-screen property viewer that shows all effective configurations for the current model with their sources — a cleaner, navigable alternative to the side panel.

**Architecture:** New `PropertyViewerScreen` that takes the existing `PropertyClaimAggregate` pipeline and renders it in a `DataTable` (one row per property) with columns: Property, Effective Value, Source Type, Source File. Selecting a row opens the existing `PropertyDetailModal`. Accessible via `v` key (currently used — move `model_properties` binding to this screen).

**Tech Stack:** Existing `PropertyClaim`/`PropertyClaimAggregate` pipeline, Textual `DataTable`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/frontend/property_viewer/__init__.py` | Create | Package marker |
| `src/dbt_tui/frontend/property_viewer/property_viewer.py` | Create | `PropertyViewerScreen` with DataTable |
| `src/dbt_tui/frontend/main.py` | Modify | Register screen; existing `v` binding already points here |
| `tests/test_property_viewer.py` | Create | Screen renders and table has rows |

---

### Task 1: PropertyViewerScreen

**Files:**
- Create: `src/dbt_tui/frontend/property_viewer/__init__.py`
- Create: `src/dbt_tui/frontend/property_viewer/property_viewer.py`
- Test: `tests/test_property_viewer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_property_viewer.py`:
```python
import pytest
from dbt_tui.frontend.main import DbtTuiFrontend
from dbt_tui.backend import DbtProject

@pytest.mark.asyncio
async def test_property_viewer_screen_mounts():
    from dbt_tui.frontend.property_viewer.property_viewer import PropertyViewerScreen
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        await pilot.press('v')
        assert isinstance(app.screen, PropertyViewerScreen)

@pytest.mark.asyncio
async def test_property_viewer_has_table():
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        await pilot.press('v')
        from textual.widgets import DataTable
        table = app.screen.query_one(DataTable)
        assert table is not None

@pytest.mark.asyncio
async def test_property_viewer_shows_no_model_message_when_empty():
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        await pilot.press('v')
        from textual.widgets import Static
        header = app.screen.query_one('#pv-header', Static)
        assert 'No model' in header.renderable or app.model is not None
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_property_viewer.py -x --tb=short -q
```

- [ ] **Step 3: Implement PropertyViewerScreen**

`src/dbt_tui/frontend/property_viewer/__init__.py` — empty.

`src/dbt_tui/frontend/property_viewer/property_viewer.py`:
```python
"""Dedicated full-screen property viewer."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Footer, Input
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.property_claim import PropertyClaimAggregate


def _build_aggregates(model) -> list[PropertyClaimAggregate]:
    """Group property claims by name into aggregates."""
    from collections import defaultdict
    by_name: dict[str, list] = defaultdict(list)
    for claim in model.property_claims:
        by_name[claim.name].append(claim)
    return [PropertyClaimAggregate(claims) for claims in by_name.values()]


_SOURCE_LABELS = {
    'dbt_project.yml': 'project',
    'schema.yml': 'schema',
    'model': 'model.sql',
}


class PropertyViewerScreen(DbtTuiScreen):
    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('/', 'focus_filter', 'Filter'),
        Binding('e', 'edit_selected', 'Edit'),
    ]

    def compose(self) -> ComposeResult:
        yield Static('', id='pv-header')
        yield Input(placeholder='Filter properties...', id='pv-filter')
        yield DataTable(id='pv-table', cursor_type='row')
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#pv-table', DataTable)
        table.add_columns('Property', 'Effective Value', 'Source', 'File', 'Overrides')
        self._refresh()

    def on_model_change(self, model) -> None:
        self._refresh()

    def _refresh(self) -> None:
        model = self.app.model
        header = self.query_one('#pv-header', Static)
        table = self.query_one('#pv-table', DataTable)
        table.clear()

        if model is None:
            header.update('No model selected — press f to search.')
            return

        header.update(f'Properties: [bold]{model.name}[/bold]')
        filter_text = self.query_one('#pv-filter', Input).value.lower()

        aggregates = _build_aggregates(model)
        for agg in sorted(aggregates, key=lambda a: a.effective.name):
            if filter_text and filter_text not in agg.effective.name.lower():
                continue
            effective = agg.effective
            source_label = _SOURCE_LABELS.get(effective.source_type, effective.source_type)
            file_name = effective.source_path.name if effective.source_path else ''
            override_count = str(len(agg.overridden)) if agg.overridden else ''
            value_str = str(effective.value)[:60]
            table.add_row(
                effective.name,
                value_str,
                source_label,
                file_name,
                override_count,
                key=effective.name,
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_focus_filter(self) -> None:
        self.query_one('#pv-filter', Input).focus()

    def action_edit_selected(self) -> None:
        table = self.query_one('#pv-table', DataTable)
        if table.cursor_row < 0:
            return
        row_key = table.get_row_at(table.cursor_row)
        # Delegate to existing PropertyDetailModal
        model = self.app.model
        if model is None:
            return
        name = row_key[0] if row_key else None
        if name:
            self._open_detail(str(name))

    def _open_detail(self, prop_name: str) -> None:
        from collections import defaultdict
        from dbt_tui.backend.property_claim import PropertyClaimAggregate
        model = self.app.model
        if model is None:
            return
        by_name: dict[str, list] = defaultdict(list)
        for claim in model.property_claims:
            by_name[claim.name].append(claim)
        if prop_name in by_name:
            from dbt_tui.frontend.model_view.properties_panel import PropertyDetailModal
            agg = PropertyClaimAggregate(by_name[prop_name])
            self.app.push_screen(PropertyDetailModal(agg))
```

- [ ] **Step 4: Register in `main.py`**

```python
from dbt_tui.frontend.property_viewer.property_viewer import PropertyViewerScreen

# SCREENS (replace existing 'model_properties' entry):
'property_viewer': PropertyViewerScreen,

# The existing binding `v` → push 'model_properties' changes to:
Binding('v', 'push_screen("property_viewer")', 'Properties'),
```

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 6: Commit**

```bash
git add src/dbt_tui/frontend/property_viewer/ \
        src/dbt_tui/frontend/main.py \
        tests/test_property_viewer.py
git commit -m "feat: add full-screen property viewer with filter and source info (v key)"
```
