# Schema.yml Editor Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users edit a model's description and tags directly from the TUI without leaving the app.

**Architecture:** New `SchemaEditorScreen` (a Textual `ModalScreen`) accessible with `e` from ModelView. Shows a two-field form: Description (`Input`) and Tags (`Input` for comma-separated list). On save, calls the existing `write_property_to_schema()` backend. After saving, refreshes the properties panel. The `property_writer.py` backend is **already complete** — this plan is purely frontend.

**Tech Stack:** Textual (`ModalScreen`, `Input`, `Button`, `Label`), existing `property_writer.py`.

---

### File map
| File | Change |
|------|--------|
| `src/dbt_tui/frontend/model_view/schema_editor.py` | Create — SchemaEditorScreen |
| `src/dbt_tui/frontend/model_view/model_view.py` | Add `e` binding + push screen |
| `src/dbt_tui/frontend/main.py` | Register `schema_editor` screen |
| `tests/test_property_writer.py` | Verify writer round-trip (backend already tested, add edge case) |

---

### Task 1: SchemaEditorScreen

**Files:**
- Create: `src/dbt_tui/frontend/model_view/schema_editor.py`

- [ ] **Step 1: Write the modal**

```python
"""Schema.yml editor modal — edit description and tags for a model."""
from __future__ import annotations
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static
from textual.containers import Vertical, Horizontal

from dbt_tui.backend.property_writer import write_property_to_schema

if TYPE_CHECKING:
    from dbt_tui.backend.model import DbtModel


class SchemaEditorScreen(ModalScreen):
    """Modal for editing a model's description and tags in schema.yml."""

    DEFAULT_CSS = """
    SchemaEditorScreen {
        align: center middle;
    }
    SchemaEditorScreen #editor-dialog {
        width: 70;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    SchemaEditorScreen Label { margin-bottom: 0; }
    SchemaEditorScreen Input { margin-bottom: 1; }
    SchemaEditorScreen #editor-buttons { height: 3; margin-top: 1; }
    SchemaEditorScreen #editor-status { height: 1; color: $text-muted; }
    """

    def __init__(self, model: 'DbtModel'):
        super().__init__()
        self._model = model

    def _get_current_description(self) -> str:
        if self._model.property_claims is None:
            return ''
        try:
            desc = self._model.property_claims.get('description')
            return str(desc) if desc else ''
        except Exception:
            return ''

    def _get_current_tags(self) -> str:
        if self._model.property_claims is None:
            return ''
        try:
            tags = self._model.property_claims.get('tags')
            if isinstance(tags, list):
                return ', '.join(str(t) for t in tags)
            return str(tags) if tags else ''
        except Exception:
            return ''

    def compose(self) -> ComposeResult:
        with Vertical(id='editor-dialog'):
            yield Label(f'Edit schema.yml — [bold]{self._model.name}[/bold]')
            yield Label('Description:')
            yield Input(
                value=self._get_current_description(),
                id='input-description',
                placeholder='Model description...',
            )
            yield Label('Tags (comma-separated):')
            yield Input(
                value=self._get_current_tags(),
                id='input-tags',
                placeholder='tag1, tag2, tag3',
            )
            yield Static('', id='editor-status')
            yield Horizontal(
                Button('Save', id='btn-save', variant='success'),
                Button('Cancel', id='btn-cancel', variant='default'),
                id='editor-buttons',
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-cancel':
            self.dismiss(False)
        elif event.button.id == 'btn-save':
            self._save()

    def _save(self) -> None:
        status = self.query_one('#editor-status', Static)
        description = self.query_one('#input-description', Input).value.strip()
        tags_raw = self.query_one('#input-tags', Input).value.strip()

        tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []

        saved_any = False
        if description:
            result = write_property_to_schema(self._model, 'description', description, 'property')
            if not result.success:
                status.update(f'[red]Error: {result.message}[/red]')
                return
            saved_any = True

        if tags:
            result = write_property_to_schema(self._model, 'tags', tags, 'config')
            if not result.success:
                status.update(f'[red]Error: {result.message}[/red]')
                return
            saved_any = True

        if saved_any:
            status.update('[green]Saved![/green]')
            self.dismiss(True)
        else:
            status.update('[yellow]Nothing to save[/yellow]')
```

---

### Task 2: Wire into ModelView and main.py

**Files:**
- Modify: `src/dbt_tui/frontend/model_view/model_view.py`
- Modify: `src/dbt_tui/frontend/main.py`

- [ ] **Step 1: Add binding to ModelView**

In `model_view.py`, add to `BINDINGS`:
```python
Binding("e", "edit_schema()", "edit schema"),
```

Add action method to `ModelView`:
```python
def action_edit_schema(self) -> None:
    """Open schema.yml editor for the current model."""
    if not self.app.model:
        return
    from .schema_editor import SchemaEditorScreen
    def on_dismiss(saved: bool) -> None:
        if saved:
            self._refresh_model_properties()
            self.app.notify("schema.yml updated")
    self.app.push_screen(SchemaEditorScreen(self.app.model), on_dismiss)
```

- [ ] **Step 2: Verify no registration needed in main.py**

`SchemaEditorScreen` is pushed directly (not via named screen), so no change to `main.py` SCREENS dict is needed.

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/dbt_tui/frontend/model_view/schema_editor.py \
        src/dbt_tui/frontend/model_view/model_view.py
git commit -m "feat(model-view): add schema.yml editor modal (e key)"
```

---

### Task 3: Test for the editor round-trip (backend)

**Files:**
- Modify: `tests/test_property_writer.py`

- [ ] **Step 1: Add round-trip test for description + tags**

Add to `tests/test_property_writer.py`:

```python
def test_write_description_and_tags_round_trip(tmp_path, vanilla_project):
    """Writing description + tags creates valid schema.yml with both fields."""
    model = vanilla_project.models[0]
    schema_path = tmp_path / 'schema.yml'

    from dbt_tui.backend.property_writer import write_property_to_schema
    r1 = write_property_to_schema(model, 'description', 'Test description', 'property', schema_path)
    assert r1.success

    r2 = write_property_to_schema(model, 'tags', ['finance', 'core'], 'config', schema_path)
    assert r2.success

    import yaml
    data = yaml.safe_load(schema_path.read_text())
    model_entry = next(m for m in data['models'] if m['name'] == model.name)
    assert model_entry['description'] == 'Test description'
    assert model_entry['config']['tags'] == ['finance', 'core']
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/test_property_writer.py -v
```
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_property_writer.py
git commit -m "test(property-writer): add description+tags round-trip test"
```
