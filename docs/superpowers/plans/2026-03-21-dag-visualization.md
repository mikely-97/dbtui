# DAG Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an ASCII DAG screen showing the dependency graph centred on the current model, navigable with arrow keys.

**Architecture:** New `DagView` screen with a `Static` widget rendering ASCII art. Backend: `DbtProject.get_dag_ascii(model, depth)` using networkx BFS + a simple box-drawing renderer. The DAG shows ancestors above, the focal model in the centre, descendants below. Current model highlighted, arrow-key navigation moves focus to a neighbour.

**Tech Stack:** NetworkX (already a dep), Textual `Static` + `ScrollableContainer`, Python string formatting.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/backend/dag.py` | Create | `render_dag_ascii(project, focal, depth)` |
| `src/dbt_tui/frontend/dag_view/__init__.py` | Create | Package marker |
| `src/dbt_tui/frontend/dag_view/dag_view.py` | Create | `DagView(DbtTuiScreen)` |
| `src/dbt_tui/frontend/main.py` | Modify | Register `dag_view` screen; bind `d` key |
| `tests/test_dag.py` | Create | Tests for ASCII renderer |

---

### Task 1: ASCII DAG renderer (backend)

**Files:**
- Create: `src/dbt_tui/backend/dag.py`
- Test: `tests/test_dag.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_dag.py`:
```python
import pytest
from dbt_tui.backend import DbtProject
from dbt_tui.backend.dag import render_dag_ascii

@pytest.fixture(scope='module')
def project():
    return DbtProject('tests/testing')

def test_focal_model_in_output(project):
    model = project.get_model_by_name('v_b')
    output = render_dag_ascii(project, model, depth=2)
    assert 'v_b' in output

def test_parent_in_output(project):
    model = project.get_model_by_name('v_b')
    output = render_dag_ascii(project, model, depth=2)
    assert 'v_a' in output

def test_child_in_output(project):
    # v_d is a downstream child of v_b (via v_c1/v_c2)
    model = project.get_model_by_name('v_b')
    output = render_dag_ascii(project, model, depth=2)
    # at depth 2 we expect at least direct children
    assert 'v_c1' in output or 'v_c2' in output

def test_depth_zero_only_focal(project):
    model = project.get_model_by_name('v_b')
    output = render_dag_ascii(project, model, depth=0)
    assert 'v_b' in output
    assert 'v_a' not in output

def test_output_is_string(project):
    model = project.get_model_by_name('v_a')
    output = render_dag_ascii(project, model, depth=1)
    assert isinstance(output, str)
    assert len(output) > 0

def test_macro_shown_as_parent(project):
    model = project.get_model_by_name('v_macro_user')
    output = render_dag_ascii(project, model, depth=1)
    assert 'clean_string' in output
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_dag.py -x --tb=short -q
```
Expected: `ModuleNotFoundError: No module named 'dbt_tui.backend.dag'`

- [ ] **Step 3: Implement `render_dag_ascii`**

Create `src/dbt_tui/backend/dag.py`:
```python
"""ASCII DAG renderer for dbt-tui."""
from __future__ import annotations
from typing import TYPE_CHECKING
import networkx as nx

if TYPE_CHECKING:
    from dbt_tui.backend.project import DbtProject
    from dbt_tui.common.entity import DbtEntityAbstract


def _ancestors_by_depth(
    graph: nx.DiGraph,
    focal,
    depth: int,
) -> dict[int, list]:
    """Return {relative_depth: [nodes]} for ancestors (negative depth = above focal)."""
    result: dict[int, list] = {}
    visited = {focal}
    frontier = [focal]
    for d in range(1, depth + 1):
        next_frontier = []
        for node in frontier:
            for pred in graph.predecessors(node):
                if pred not in visited:
                    visited.add(pred)
                    next_frontier.append(pred)
        if not next_frontier:
            break
        result[-d] = sorted(next_frontier, key=lambda n: n.name)
        frontier = next_frontier
    return result


def _descendants_by_depth(
    graph: nx.DiGraph,
    focal,
    depth: int,
) -> dict[int, list]:
    result: dict[int, list] = {}
    visited = {focal}
    frontier = [focal]
    for d in range(1, depth + 1):
        next_frontier = []
        for node in frontier:
            for succ in graph.successors(node):
                if succ not in visited:
                    visited.add(succ)
                    next_frontier.append(succ)
        if not next_frontier:
            break
        result[d] = sorted(next_frontier, key=lambda n: n.name)
        frontier = next_frontier
    return result


def _format_node(entity, focal, width: int = 20) -> str:
    label = entity.name
    if entity.entity_type != 'model':
        label = f'[{entity.entity_type[0]}] {label}'
    if entity == focal:
        return f'[ {label} ]'.center(width)
    return label.center(width)


def render_dag_ascii(
    project: DbtProject,
    focal: DbtEntityAbstract,
    depth: int = 2,
) -> str:
    graph = project.graph
    ancestors = _ancestors_by_depth(graph, focal, depth)
    descendants = _descendants_by_depth(graph, focal, depth)

    lines: list[str] = []

    # Ancestors (deepest first so they appear at top)
    for d in sorted(ancestors.keys()):  # -depth … -1
        nodes = ancestors[d]
        lines.append('  '.join(_format_node(n, focal) for n in nodes))
        lines.append('  '.join('     |     '.center(20) for _ in nodes))

    # Focal
    lines.append(_format_node(focal, focal, width=24))

    # Descendants
    for d in sorted(descendants.keys()):  # 1 … depth
        nodes = descendants[d]
        lines.append('  '.join('     |     '.center(20) for _ in nodes))
        lines.append('  '.join(_format_node(n, focal) for n in nodes))

    return '\n'.join(lines)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_dag.py -x --tb=short -q
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/backend/dag.py tests/test_dag.py
git commit -m "feat: add ASCII DAG renderer"
```

---

### Task 2: DagView screen

**Files:**
- Create: `src/dbt_tui/frontend/dag_view/__init__.py`
- Create: `src/dbt_tui/frontend/dag_view/dag_view.py`
- Modify: `src/dbt_tui/frontend/main.py`

- [ ] **Step 1: Write failing test**

In `tests/test_frontend.py`:
```python
@pytest.mark.asyncio
async def test_dag_view_screen_renders():
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        await pilot.press('d')  # open DAG view
        from dbt_tui.frontend.dag_view.dag_view import DagView
        assert isinstance(app.screen, DagView)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_frontend.py::test_dag_view_screen_renders -x --tb=short
```

- [ ] **Step 3: Create DagView screen**

`src/dbt_tui/frontend/dag_view/__init__.py` — empty.

`src/dbt_tui/frontend/dag_view/dag_view.py`:
```python
from textual.app import ComposeResult
from textual.widgets import Static, Footer, Input
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.binding import Binding

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.dag import render_dag_ascii


class DagView(DbtTuiScreen):
    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('+', 'increase_depth', 'More depth'),
        Binding('-', 'decrease_depth', 'Less depth'),
    ]

    def __init__(self):
        super().__init__()
        self._depth = 2

    def compose(self) -> ComposeResult:
        yield Static('DAG View', id='dag-title')
        yield Static('depth: 2  (+/-  to change)', id='dag-controls')
        yield ScrollableContainer(Static('', id='dag-content'))
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_dag()

    def on_model_change(self, model) -> None:
        self._refresh_dag()

    def _refresh_dag(self) -> None:
        model = self.app.model
        project = self.app.project
        content = self.query_one('#dag-content', Static)
        controls = self.query_one('#dag-controls', Static)
        controls.update(f'depth: {self._depth}  (+/- to change)')
        if model is None or project is None:
            content.update('No model selected.')
            return
        text = render_dag_ascii(project, model, depth=self._depth)
        content.update(text)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_increase_depth(self) -> None:
        self._depth = min(self._depth + 1, 6)
        self._refresh_dag()

    def action_decrease_depth(self) -> None:
        self._depth = max(self._depth - 1, 0)
        self._refresh_dag()
```

- [ ] **Step 4: Register in `main.py`**

```python
# In SCREENS dict:
'dag_view': DagView,

# In BINDINGS:
Binding('d', 'push_screen("dag_view")', 'DAG'),
```

Add import:
```python
from dbt_tui.frontend.dag_view.dag_view import DagView
```

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 6: Commit**

```bash
git add src/dbt_tui/frontend/dag_view/ src/dbt_tui/frontend/main.py tests/test_frontend.py
git commit -m "feat: add DAG visualization screen (d key)"
```
