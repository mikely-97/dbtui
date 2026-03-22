# Keyboard Shortcut Help Screen Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Press `?` anywhere in the app to see a full list of keyboard shortcuts.

**Architecture:** New `HelpScreen` (`ModalScreen`) shows a `DataTable` with columns (Context, Key, Action). Bindings are hardcoded from each screen — this is simpler and more maintainable than introspecting `BINDINGS` at runtime. Registered in `main.py`; `?` binding added globally.

**Tech Stack:** Textual (`ModalScreen`, `DataTable`), no new dependencies.

---

### File map
| File | Change |
|------|--------|
| `src/dbt_tui/frontend/help_screen/help_screen.py` | Create — HelpScreen modal |
| `src/dbt_tui/frontend/help_screen/__init__.py` | Create — package |
| `src/dbt_tui/frontend/main.py` | Add `?` binding, register screen |

---

### Task 1: HelpScreen

**Files:**
- Create: `src/dbt_tui/frontend/help_screen/__init__.py`
- Create: `src/dbt_tui/frontend/help_screen/help_screen.py`

- [ ] **Step 1: Create package init**

Create `src/dbt_tui/frontend/help_screen/__init__.py`:
```python
```
(empty file)

- [ ] **Step 2: Create HelpScreen**

Create `src/dbt_tui/frontend/help_screen/help_screen.py`:

```python
"""Keyboard shortcut help modal."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Label
from textual.containers import Vertical


# All bindings in the application, grouped by context.
# Format: (context, key, description)
ALL_BINDINGS: list[tuple[str, str, str]] = [
    # Global
    ('Global', 'q', 'Quit'),
    ('Global', 'o', 'Options'),
    ('Global', 'f', 'Find model'),
    ('Global', 'p', 'Change project'),
    ('Global', 'v', 'Property viewer'),
    ('Global', 'd', 'DAG view'),
    ('Global', 'l', 'Column lineage'),
    ('Global', '?', 'This help screen'),
    # Model view
    ('Model View', 'r', 'Run model'),
    ('Model View', 't', 'Test model'),
    ('Model View', 'R', 'Refresh properties'),
    ('Model View', 'E', 'Open in external editor'),
    ('Model View', 'e', 'Edit schema.yml'),
    ('Model View', 'enter', 'Enter edit mode (in SQL editor)'),
    ('Model View', 'escape', 'Exit edit mode / save'),
    ('Model View', '→ / l', 'Focus properties panel'),
    ('Model View', '← / h', 'Focus SQL editor'),
    ('Model View', 'tab', 'Next pane'),
    # DAG view
    ('DAG View', '+', 'Increase depth'),
    ('DAG View', '-', 'Decrease depth'),
    ('DAG View', 'enter', 'Navigate to selected node'),
    ('DAG View', 'escape', 'Back'),
    # Model search
    ('Model Search', '↓ / j', 'Next result'),
    ('Model Search', '↑ / k', 'Previous result'),
    ('Model Search', 'enter', 'Select model'),
    ('Model Search', 'escape', 'Back'),
    # Property viewer
    ('Property Viewer', '/', 'Filter properties'),
    ('Property Viewer', 'escape', 'Back'),
    # Column lineage
    ('Lineage View', 'escape', 'Back'),
]


class HelpScreen(ModalScreen):
    """Full shortcut reference."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen #help-dialog {
        width: 80;
        height: 80%;
        max-height: 50;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    HelpScreen Label {
        text-style: bold;
        margin-bottom: 1;
    }
    HelpScreen DataTable { height: 1fr; }
    """

    BINDINGS = [
        Binding('escape', 'dismiss_help', 'Close', show=True),
        Binding('?', 'dismiss_help', 'Close', show=False),
        Binding('q', 'dismiss_help', 'Close', show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='help-dialog'):
            yield Label('Keyboard Shortcuts  (Esc to close)')
            yield DataTable(id='help-table', zebra_stripes=True, show_cursor=False)

    def on_mount(self) -> None:
        table = self.query_one('#help-table', DataTable)
        table.add_columns('Context', 'Key', 'Action')
        for context, key, action in ALL_BINDINGS:
            table.add_row(context, f'[bold]{key}[/bold]', action)

    def action_dismiss_help(self) -> None:
        self.dismiss()
```

---

### Task 2: Wire into main.py

**Files:**
- Modify: `src/dbt_tui/frontend/main.py`

- [ ] **Step 1: Add import**

Add near the top of `main.py`:
```python
from .help_screen.help_screen import HelpScreen
```

- [ ] **Step 2: Add binding**

In `DbtTuiFrontend.BINDINGS`, add:
```python
Binding("?", "push_screen('help')", "help"),
```

- [ ] **Step 3: Register screen**

In `DbtTuiFrontend.SCREENS`, add:
```python
'help': HelpScreen,
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/frontend/help_screen/ \
        src/dbt_tui/frontend/main.py
git commit -m "feat: add keyboard shortcut help screen (? key)"
```
