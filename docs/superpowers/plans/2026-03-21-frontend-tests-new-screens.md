# Frontend Tests for New Screens Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Textual Pilot tests for DagView, ColumnLineageView, PropertyViewerScreen, and the multi-project workspace tab bar.

**Architecture:** Follow the existing test pattern in `tests/test_frontend.py` and `tests/test_model_view.py` — use `app.run_test()` with an async `Pilot`, set `app.project` and `app.model` before pushing screens, then assert widget content.

**Tech Stack:** pytest-asyncio, Textual `Pilot`, existing `DbtTuiFrontend`.

---

### File map
| File | Change |
|------|--------|
| `tests/test_frontend_new_screens.py` | Create — tests for new screens |

---

### Task 1: DagView tests

**Files:**
- Create: `tests/test_frontend_new_screens.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for new screens added in 0.3.0: DagView, ColumnLineageView, PropertyViewerScreen, workspace."""
import pytest
from textual.pilot import Pilot

from dbt_tui.frontend.main import DbtTuiFrontend


@pytest.fixture
def app_with_project(vanilla_project):
    """DbtTuiFrontend pre-loaded with a project and first model."""
    app = DbtTuiFrontend()
    app._test_project = vanilla_project
    return app


# ── DagView ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dag_view_mounts(vanilla_project):
    """DagView renders without errors when a model is selected."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        await pilot.press('d')
        await pilot.pause()
        # Title should contain the model name
        from textual.widgets import Static
        title = app.query_one('#dag-title', Static)
        assert vanilla_project.models[0].name in title.renderable


@pytest.mark.asyncio
async def test_dag_view_depth_increases(vanilla_project):
    """+ key increases depth label."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        await pilot.press('d')
        await pilot.pause()
        from textual.widgets import Static
        controls = app.query_one('#dag-controls', Static)
        assert 'depth: 2' in str(controls.renderable)
        await pilot.press('+')
        await pilot.pause()
        assert 'depth: 3' in str(controls.renderable)


@pytest.mark.asyncio
async def test_dag_view_node_list_populated(vanilla_project):
    """Node list is populated with at least the focal model."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        await pilot.press('d')
        await pilot.pause()
        from textual.widgets import ListView
        node_list = app.query_one('#dag-node-list', ListView)
        assert len(node_list.children) > 0


@pytest.mark.asyncio
async def test_dag_view_escape_pops_screen(vanilla_project):
    """Escape closes DagView."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        initial_depth = len(app.screen_stack)
        await pilot.press('d')
        await pilot.pause()
        assert len(app.screen_stack) > initial_depth
        await pilot.press('escape')
        await pilot.pause()
        assert len(app.screen_stack) == initial_depth


# ── ColumnLineageView ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lineage_view_mounts(vanilla_project):
    """ColumnLineageView renders a DataTable without errors."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        await pilot.press('l')
        await pilot.pause()
        from textual.widgets import DataTable
        table = app.query_one(DataTable)
        assert table is not None


@pytest.mark.asyncio
async def test_lineage_view_escape_closes(vanilla_project):
    """Escape closes ColumnLineageView."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        depth_before = len(app.screen_stack)
        await pilot.press('l')
        await pilot.pause()
        await pilot.press('escape')
        await pilot.pause()
        assert len(app.screen_stack) == depth_before


# ── PropertyViewerScreen ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_property_viewer_mounts(vanilla_project):
    """PropertyViewerScreen renders a DataTable."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        await pilot.press('v')
        await pilot.pause()
        from textual.widgets import DataTable
        table = app.query_one(DataTable)
        assert table is not None


@pytest.mark.asyncio
async def test_property_viewer_escape_closes(vanilla_project):
    """Escape closes PropertyViewerScreen."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        app.model = vanilla_project.models[0]
        depth_before = len(app.screen_stack)
        await pilot.press('v')
        await pilot.pause()
        await pilot.press('escape')
        await pilot.pause()
        assert len(app.screen_stack) == depth_before


# ── Workspace / ProjectTabBar ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_project_tab_bar_mounts(vanilla_project):
    """ProjectTabBar is present after mount."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        await pilot.pause()
        from dbt_tui.frontend.common.project_tab_bar import ProjectTabBar
        tab_bar = app.query_one('#project-tab-bar', ProjectTabBar)
        assert tab_bar is not None


@pytest.mark.asyncio
async def test_add_project_creates_second_entry(vanilla_project):
    """add_project() appends to projects list and switches active project."""
    app = DbtTuiFrontend()
    async with app.run_test(size=(120, 40)) as pilot:
        app.project = vanilla_project
        await pilot.pause()
        assert len(app.projects) >= 1
        initial = len(app.projects)
        # Add the same project again (simplest available project)
        app.add_project(vanilla_project)
        assert len(app.projects) == initial + 1
```

- [ ] **Step 2: Run tests to verify they exist and some pass**

```bash
pytest tests/test_frontend_new_screens.py -v --timeout=30
```
Expected: most pass; fix any import or widget-query errors.

- [ ] **Step 3: Run full suite**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_frontend_new_screens.py
git commit -m "test(frontend): add Pilot tests for DagView, LineageView, PropertyViewer, workspace"
```
