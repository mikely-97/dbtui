# DAG Keyboard Navigation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users navigate the DAG with arrow keys and press Enter to jump to any related model.

**Architecture:** Keep the existing ASCII art display. Add a navigable node-list panel beneath it (a `ListView`). A new backend helper collects all in-scope nodes ordered by depth (ancestors first, focal, then descendants). Pressing Enter on a list item sets `app.model`, which pops DagView and opens that model.

**Tech Stack:** Textual (`ListView`, `ListItem`, `Label`), existing `dag.py` `_walk_by_depth`.

---

### File map
| File | Change |
|------|--------|
| `src/dbt_tui/backend/dag.py` | Add `get_dag_node_list()` helper |
| `src/dbt_tui/frontend/dag_view/dag_view.py` | Add ListView panel + select handler |
| `tests/test_dag.py` | Add test for `get_dag_node_list` |

---

### Task 1: Backend helper — `get_dag_node_list`

**Files:**
- Modify: `src/dbt_tui/backend/dag.py`
- Test: `tests/test_dag.py`

- [ ] **Step 1: Write failing test**

In `tests/test_dag.py`, add:

```python
from dbt_tui.backend.dag import get_dag_node_list

def test_get_dag_node_list_returns_all_related_nodes(vanilla_project):
    """Node list includes ancestors, focal, and descendants in depth order."""
    # pick a model with known parents/children
    model = vanilla_project.get_model_by_name('stg_orders')
    nodes = get_dag_node_list(vanilla_project, model, depth=2)
    names = [n.name for n in nodes]
    # focal model must be in the list
    assert 'stg_orders' in names
    # result is a list of DbtEntityAbstract
    from dbt_tui.common.entity import DbtEntityAbstract
    for n in nodes:
        assert isinstance(n, DbtEntityAbstract)

def test_get_dag_node_list_focal_only_when_isolated(vanilla_project):
    """A node with no connections still appears in the list."""
    model = vanilla_project.models[0]
    nodes = get_dag_node_list(vanilla_project, model, depth=2)
    assert model in nodes
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/test_dag.py::test_get_dag_node_list_returns_all_related_nodes -v
```
Expected: FAIL — `ImportError: cannot import name 'get_dag_node_list'`

- [ ] **Step 3: Implement `get_dag_node_list`**

Add to `src/dbt_tui/backend/dag.py`:

```python
def get_dag_node_list(project: 'DbtProject', focal: 'DbtEntityAbstract', depth: int = 2) -> list['DbtEntityAbstract']:
    """Return nodes visible in DAG ordered: ancestors (deep→shallow), focal, descendants (shallow→deep)."""
    graph = project.graph
    ancestors = _walk_by_depth(graph, focal, depth, graph.predecessors)
    descendants = _walk_by_depth(graph, focal, depth, graph.successors)

    result: list['DbtEntityAbstract'] = []
    for d in sorted(ancestors.keys()):        # -depth … -1
        result.extend(ancestors[d])
    result.append(focal)
    for d in sorted(descendants.keys()):      # 1 … depth
        result.extend(descendants[d])
    return result
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_dag.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/backend/dag.py tests/test_dag.py
git commit -m "feat(dag): add get_dag_node_list helper"
```

---

### Task 2: DagView — navigable node list panel

**Files:**
- Modify: `src/dbt_tui/frontend/dag_view/dag_view.py`

The current layout is: `dag-title` → `dag-controls` → `ScrollableContainer(dag-content)` → `Footer`.

We add a `ListView` at the bottom labelled "Navigate → (Enter to jump)".

- [ ] **Step 1: Update imports and compose**

Replace the entire file content:

```python
from textual.app import ComposeResult
from textual.widgets import Static, Footer, ListView, ListItem, Label
from textual.containers import ScrollableContainer
from textual.binding import Binding

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.dag import render_dag_ascii, get_dag_node_list


class DagView(DbtTuiScreen):
    DEFAULT_CSS = """
    DagView #dag-node-list { height: 8; border: solid $accent; }
    DagView #dag-nav-label { height: 1; color: $text-muted; }
    """

    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('+', 'increase_depth', 'More depth'),
        Binding('-', 'decrease_depth', 'Less depth'),
    ]

    def __init__(self):
        super().__init__()
        self._depth = 2
        self._nav_nodes: list = []

    def compose(self) -> ComposeResult:
        yield Static('', id='dag-title')
        yield Static('depth: 2  (+ / - to change)', id='dag-controls')
        yield ScrollableContainer(Static('', id='dag-content'))
        yield Static('Navigate (↑↓ Enter to jump):', id='dag-nav-label')
        yield ListView(id='dag-node-list')
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_dag()

    def on_model_change(self, model) -> None:
        self._refresh_dag()

    def _refresh_dag(self) -> None:
        model = self.app.model
        project = self.app.project
        controls = self.query_one('#dag-controls', Static)
        controls.update(f'depth: {self._depth}  (+ / - to change)')
        content = self.query_one('#dag-content', Static)
        node_list = self.query_one('#dag-node-list', ListView)

        if model is None or project is None:
            content.update('No model selected — press f to search.')
            node_list.clear()
            self._nav_nodes = []
            return

        title = self.query_one('#dag-title', Static)
        title.update(f'DAG: {model.name}')
        text = render_dag_ascii(project, model, depth=self._depth)
        content.update(text)

        # Populate navigation list
        self._nav_nodes = get_dag_node_list(project, model, depth=self._depth)
        node_list.clear()
        for node in self._nav_nodes:
            marker = '► ' if node is model else '  '
            label = f"{marker}{node.name} [{node.entity_type}]"
            node_list.append(ListItem(Label(label)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Navigate to the selected node when Enter is pressed."""
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._nav_nodes):
            target = self._nav_nodes[idx]
            from dbt_tui.backend.model import DbtModel
            if isinstance(target, DbtModel):
                self.app.model = target

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_increase_depth(self) -> None:
        self._depth = min(self._depth + 1, 6)
        self._refresh_dag()

    def action_decrease_depth(self) -> None:
        self._depth = max(self._depth - 1, 0)
        self._refresh_dag()
```

- [ ] **Step 2: Run all tests**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/dbt_tui/frontend/dag_view/dag_view.py
git commit -m "feat(dag): add keyboard navigation list to DagView"
```
