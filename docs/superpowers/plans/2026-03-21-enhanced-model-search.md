# Enhanced Model Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve model search with better fuzzy scoring, entity-type filters, tag filters, and path filters.

**Architecture:** Extend `DbtProject.search_entities()` with a scored, multi-field search that accepts filter kwargs. Add filter toggles to `ModelSearch` screen using Textual `Checkbox` widgets above the search input.

**Tech Stack:** Python `difflib.SequenceMatcher`, Textual `Checkbox`, existing `DbtProject`/`DbtEntityAbstract` abstractions.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/backend/project.py` | Modify | Rewrite `search_entities` with scored fuzzy + filters |
| `src/dbt_tui/common/project.py` | Modify | Update abstract signature to accept filter kwargs |
| `src/dbt_tui/frontend/model_search/model_search.py` | Modify | Add filter bar (entity type, path prefix) |
| `src/dbt_tui/frontend/model_search/model_search.tcss` | Create/Modify | Style the filter bar |
| `tests/test_search_and_cache.py` | Modify | Add tests for filtered/scored search |

---

### Task 1: Improve fuzzy scoring in backend

**Files:**
- Modify: `src/dbt_tui/backend/project.py` — `search_entities` method
- Test: `tests/test_search_and_cache.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_search_and_cache.py`:
```python
def test_search_scores_exact_prefix_higher(project):
    """'v_a' should rank exact-prefix matches above partial matches."""
    results = project.search_entities('v_a', entity_type='model')
    names = [r.name for r in results]
    assert names[0] == 'v_a'

def test_search_filters_by_entity_type_model(project):
    results = project.search_entities('clean', entity_type='macro')
    assert all(r.entity_type == 'macro' for r in results)
    assert any(r.name == 'clean_string' for r in results)

def test_search_filters_by_entity_type_excludes_others(project):
    results = project.search_entities('v_a', entity_type='macro')
    assert all(r.entity_type == 'macro' for r in results)

def test_search_path_prefix_filter(project):
    results = project.search_entities('', path_prefix='vanilla/stg')
    assert all('vanilla/stg' in str(r.file_path_relative) for r in results)

def test_search_empty_query_returns_all(project):
    results = project.search_entities('')
    assert len(results) >= len(project.models)

def test_search_returns_macros_when_no_filter(project):
    results = project.search_entities('clean_string')
    names = [r.name for r in results]
    assert 'clean_string' in names
```

- [ ] **Step 2: Run to verify tests fail**

```bash
pytest tests/test_search_and_cache.py -x --tb=short -q
```
Expected: several failures (current `search_entities` doesn't accept `path_prefix` etc.)

- [ ] **Step 3: Rewrite `search_entities` in `backend/project.py`**

Replace `search_entities` with:
```python
def search_entities(
    self,
    query: str,
    entity_type: str | None = None,
    path_prefix: str | None = None,
) -> list[DbtEntityAbstract]:
    """Fuzzy search across models and macros with optional filters."""
    from difflib import SequenceMatcher

    # Build candidate pool
    candidates: list[DbtEntityAbstract] = []
    if entity_type is None or entity_type == 'model':
        candidates.extend(self.models)
    if entity_type is None or entity_type == 'macro':
        candidates.extend(self.macros)

    # Apply path prefix filter
    if path_prefix:
        candidates = [
            c for c in candidates
            if path_prefix in str(c.file_path_relative)
        ]

    if not query:
        return sorted(candidates, key=lambda c: c.name)

    q = query.lower()

    def score(entity: DbtEntityAbstract) -> float:
        name = entity.name.lower()
        if name == q:
            return 1.0
        if name.startswith(q):
            return 0.9 + len(q) / len(name) * 0.09
        if q in name:
            return 0.7 + len(q) / len(name) * 0.19
        return SequenceMatcher(None, q, name).ratio() * 0.6

    scored = [(score(c), c) for c in candidates]
    scored = [(s, c) for s, c in scored if s > 0.3]
    scored.sort(key=lambda x: (-x[0], x[1].name))
    return [c for _, c in scored]
```

Also update `search_models` to delegate:
```python
def search_models(self, query: str) -> list[DbtModel]:
    return [e for e in self.search_entities(query, entity_type='model')
            if isinstance(e, DbtModel)]
```

- [ ] **Step 4: Update abstract signature in `common/project.py`**

```python
@abstractmethod
def search_entities(
    self,
    query: str,
    entity_type: str | None = None,
    path_prefix: str | None = None,
) -> list:
    ...
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_search_and_cache.py -x --tb=short -q
```
Expected: all new tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/dbt_tui/backend/project.py src/dbt_tui/common/project.py tests/test_search_and_cache.py
git commit -m "feat: improve search scoring and add entity_type/path_prefix filters"
```

---

### Task 2: Add entity-type filter bar to ModelSearch screen

**Files:**
- Modify: `src/dbt_tui/frontend/model_search/model_search.py`
- Create: `src/dbt_tui/frontend/model_search/model_search.tcss` (if not exists)
- Test: `tests/test_frontend.py`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_model_search_has_filter_checkboxes():
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        # Push ModelSearch screen
        await pilot.press('f')
        screen = app.screen
        assert screen.query_one('#filter-models') is not None
        assert screen.query_one('#filter-macros') is not None
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_frontend.py::test_model_search_has_filter_checkboxes -x --tb=short
```

- [ ] **Step 3: Add filter bar to `ModelSearch`**

In `frontend/model_search/model_search.py`, modify `compose()`:
```python
from textual.widgets import Checkbox

def compose(self) -> ComposeResult:
    yield Horizontal(
        Checkbox("Models", value=True, id="filter-models"),
        Checkbox("Macros", value=True, id="filter-macros"),
        id="search-filters",
    )
    yield Horizontal(
        ModelSearchList(id="model_list"),
        ScrollableContainer(TextArea(id="model_preview")),
    )
    yield ModelSearchInput(placeholder="Search models...", id="search_input")
    yield Footer()
```

Add handler:
```python
def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
    self._do_search()

def _do_search(self) -> None:
    query = self.query_one('#search_input', ModelSearchInput).value
    entity_type = self._active_entity_type()
    if self.app.project:
        results = self.app.project.search_entities(query, entity_type=entity_type)
        self.query_one('#model_list', ModelSearchList).update(results)

def _active_entity_type(self) -> str | None:
    models = self.query_one('#filter-models', Checkbox).value
    macros = self.query_one('#filter-macros', Checkbox).value
    if models and not macros:
        return 'model'
    if macros and not models:
        return 'macro'
    return None
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/ -x --tb=short -q
```

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/frontend/model_search/ tests/test_frontend.py
git commit -m "feat: add entity-type filter checkboxes to model search screen"
```
