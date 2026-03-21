# Multiple Project Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow the user to have multiple dbt projects open simultaneously, switching between them with a tab bar, with each project keeping its own last-active model.

**Architecture:** Replace the single `app.project` reactive with `app.projects: list[DbtProject]` + `app.active_project_index: reactive[int]`. The top of every screen gains a `ProjectTabBar` widget showing project names as clickable tabs. `DbtTuiCache` gains a `workspaces: list[WorkspaceEntry]` field. The existing `DbtProjectAbstract` / `DbtModel` interfaces are unchanged.

**Tech Stack:** Textual `reactive`, existing `DbtProject`, updated `DbtTuiCache`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/common/cache.py` | Modify | Add `workspaces: list[WorkspaceEntry]` field |
| `src/dbt_tui/frontend/common/project_tab_bar.py` | Create | `ProjectTabBar` widget |
| `src/dbt_tui/frontend/main.py` | Modify | `projects` list + `active_project_index` reactive; update all project/model wiring |
| `tests/test_workspace.py` | Create | Tests for workspace cache and project switching |

---

### Task 1: WorkspaceEntry in cache

**Files:**
- Modify: `src/dbt_tui/common/cache.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_workspace.py`:
```python
import pytest
from dbt_tui.common.cache import DbtTuiCache, WorkspaceEntry, load_cache, save_cache

def test_workspace_entry_has_fields():
    w = WorkspaceEntry(project_path='/some/path', last_model='my_model')
    assert w.project_path == '/some/path'
    assert w.last_model == 'my_model'

def test_cache_has_workspaces_field():
    cache = DbtTuiCache()
    assert hasattr(cache, 'workspaces')
    assert isinstance(cache.workspaces, list)

def test_workspace_roundtrip(tmp_path):
    """Cache with workspaces serializes and deserializes correctly."""
    from unittest.mock import patch
    cache = DbtTuiCache(
        workspaces=[
            WorkspaceEntry(project_path='/a/project', last_model='my_model'),
            WorkspaceEntry(project_path='/b/project', last_model=None),
        ]
    )
    cache_file = tmp_path / 'cache.json'
    with patch('dbt_tui.common.cache.ensure_cache_path', return_value=cache_file):
        save_cache(cache)
        loaded = load_cache()
    assert len(loaded.workspaces) == 2
    assert loaded.workspaces[0].project_path == '/a/project'
    assert loaded.workspaces[0].last_model == 'my_model'

def test_empty_cache_has_empty_workspaces():
    cache = DbtTuiCache()
    assert cache.workspaces == []
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_workspace.py -x --tb=short -q
```

- [ ] **Step 3: Update `cache.py`**

In `src/dbt_tui/common/cache.py`:

```python
from dataclasses import dataclass, field
from typing import Any
import json
from pathlib import Path
from platformdirs import user_cache_dir


@dataclass
class WorkspaceEntry:
    project_path: str
    last_model: str | None = None


@dataclass
class DbtTuiCache:
    last_open_project_raw: str | None = None   # legacy single-project field
    last_active_model: str | None = None        # legacy field
    external_editor_command: str = 'vi'
    workspaces: list[WorkspaceEntry] = field(default_factory=list)

    @property
    def last_open_project(self) -> Path | None:
        if self.last_open_project_raw:
            return Path(self.last_open_project_raw)
        return None
```

Update `save_cache`/`load_cache` to handle `workspaces` serialization:
```python
def _cache_to_dict(cache: DbtTuiCache) -> dict:
    return {
        'last_open_project_raw': cache.last_open_project_raw,
        'last_active_model': cache.last_active_model,
        'external_editor_command': cache.external_editor_command,
        'workspaces': [
            {'project_path': w.project_path, 'last_model': w.last_model}
            for w in cache.workspaces
        ],
    }

def _dict_to_cache(data: dict) -> DbtTuiCache:
    workspaces = [
        WorkspaceEntry(**w)
        for w in data.get('workspaces', [])
    ]
    return DbtTuiCache(
        last_open_project_raw=data.get('last_open_project_raw'),
        last_active_model=data.get('last_active_model'),
        external_editor_command=data.get('external_editor_command', 'vi'),
        workspaces=workspaces,
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_workspace.py -x --tb=short -q
```

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/common/cache.py tests/test_workspace.py
git commit -m "feat: add WorkspaceEntry to DbtTuiCache for multi-project support"
```

---

### Task 2: ProjectTabBar widget

**Files:**
- Create: `src/dbt_tui/frontend/common/project_tab_bar.py`

- [ ] **Step 1: Create ProjectTabBar**

`src/dbt_tui/frontend/common/project_tab_bar.py`:
```python
"""Tab bar for switching between open projects."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Button, Static
from textual.containers import Horizontal
from textual.widget import Widget
from textual.message import Message


class ProjectTabBar(Widget):
    """Horizontal tab bar showing open projects."""

    DEFAULT_CSS = """
    ProjectTabBar {
        height: 3;
        background: $panel;
    }
    ProjectTabBar Button {
        min-width: 16;
        height: 3;
    }
    ProjectTabBar Button.-active {
        background: $accent;
    }
    ProjectTabBar #add-project-btn {
        min-width: 3;
    }
    """

    class ProjectSelected(Message):
        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class AddProjectRequested(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Horizontal(id='tabs-row')
        yield Button('+', id='add-project-btn', variant='default')

    def refresh_projects(self, projects, active_index: int) -> None:
        row = self.query_one('#tabs-row', Horizontal)
        row.remove_children()
        for i, project in enumerate(projects):
            name = project.root_folder.name
            btn = Button(name, id=f'tab-{i}', classes='-active' if i == active_index else '')
            row.mount(btn)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'add-project-btn':
            self.post_message(self.AddProjectRequested())
        elif event.button.id and event.button.id.startswith('tab-'):
            idx = int(event.button.id.split('-')[1])
            self.post_message(self.ProjectSelected(idx))
```

- [ ] **Step 2: Commit**

```bash
git add src/dbt_tui/frontend/common/project_tab_bar.py
git commit -m "feat: add ProjectTabBar widget for workspace switching"
```

---

### Task 3: Wire multi-project into App

**Files:**
- Modify: `src/dbt_tui/frontend/main.py`

- [ ] **Step 1: Write failing test**

In `tests/test_workspace.py`:
```python
@pytest.mark.asyncio
async def test_app_has_projects_list():
    from dbt_tui.frontend.main import DbtTuiFrontend
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        assert hasattr(app, 'projects')
        assert isinstance(app.projects, list)

@pytest.mark.asyncio
async def test_app_can_add_second_project():
    from dbt_tui.frontend.main import DbtTuiFrontend
    from dbt_tui.backend import DbtProject
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        p = DbtProject('tests/testing')
        app.add_project(p)
        assert len(app.projects) >= 1
```

- [ ] **Step 2: Update `main.py`**

Key changes:

```python
# Replace single project reactive:
projects: reactive[list[DbtProject]] = reactive([], recompose=True)
active_project_index: reactive[int] = reactive(0)

@property
def project(self) -> DbtProject | None:
    """Convenience property — the currently active project."""
    if not self.projects or self.active_project_index >= len(self.projects):
        return None
    return self.projects[self.active_project_index]

def add_project(self, project: DbtProject) -> None:
    self.projects = [*self.projects, project]
    self.active_project_index = len(self.projects) - 1

def watch_active_project_index(self, new: int) -> None:
    # Notify all screens of project change
    for screen in self.screen_stack:
        if hasattr(screen, 'on_project_change'):
            screen.on_project_change(self.project)
    # Restore last model for this workspace
    cache = load_cache()
    if new < len(cache.workspaces):
        ws = cache.workspaces[new]
        if ws.last_model and self.project:
            try:
                self.model = self.project.get_model_by_name(ws.last_model)
            except Exception:
                self.model = None
```

- [ ] **Step 3: Add ProjectTabBar to base screen**

In `DbtTuiScreen`, add `ProjectTabBar` to the top of every screen (or in the App's `compose`):

```python
# In DbtTuiFrontend.compose():
yield ProjectTabBar(id='project-tab-bar')
yield ContentSwitcher(...)  # existing screen content
```

Or mount it in each screen's `compose` — the former is cleaner.

- [ ] **Step 4: Save workspace on model/project change**

In `save_context_debounced`:
```python
def save_context_debounced(self) -> None:
    # Update workspaces list
    workspaces = []
    for i, proj in enumerate(self.projects):
        last_model = None
        if i == self.active_project_index and self.model:
            last_model = self.model.name
        workspaces.append(WorkspaceEntry(
            project_path=str(proj.root_folder),
            last_model=last_model,
        ))
    cache = load_cache()
    cache.workspaces = workspaces
    save_cache(cache)
```

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 6: Commit**

```bash
git add src/dbt_tui/frontend/main.py tests/test_workspace.py
git commit -m "feat: wire multi-project workspace into App with tab switching"
```
