# Model Search by Tag / Materialization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users filter the model search by tag or materialization type (view / table / incremental / ephemeral).

**Architecture:** Add `tags` and `materialized` properties to `DbtModel` by reading the `config()` Jinja call (same pattern used for `name`). Extend `search_entities` on `DbtProject` to accept `tag` and `materialized` keyword filters. Add a second filter row to `ModelSearch` with a tag `Input` and a materialization `Select`. Hook into `_do_search`.

**Tech Stack:** Textual (`Input`, `Select`), existing Jinja AST parsing in `DbtModel`, existing `search_entities` in `DbtProject`.

---

### File map
| File | Change |
|------|--------|
| `src/dbt_tui/backend/model.py` | Add `tags` + `materialized` properties |
| `src/dbt_tui/backend/project.py` | Add `tag`/`materialized` params to `search_entities` |
| `src/dbt_tui/common/project.py` | Update abstract `search_entities` signature |
| `src/dbt_tui/frontend/model_search/model_search.py` | Add tag input + mat filter row |
| `src/dbt_tui/frontend/model_search/model_search_input.py` | Read new filters in `_do_search` |
| `tests/test_project_methods.py` | Add tag/materialization filter tests |

---

### Task 1: Backend — `tags` and `materialized` on DbtModel

**Files:**
- Modify: `src/dbt_tui/backend/model.py`
- Modify: `tests/test_project_methods.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_project_methods.py`:

```python
def test_model_tags_empty_by_default(vanilla_project):
    """Model with no config() tags returns empty list."""
    # pick a model that has no config() or no tags kwarg
    model = vanilla_project.models[0]
    assert isinstance(model.tags, list)


def test_model_materialized_defaults_to_view(vanilla_project):
    """Model without config(materialized=...) returns 'view'."""
    model = vanilla_project.models[0]
    assert model.materialized in ('view', 'table', 'incremental', 'ephemeral', None)


def test_search_by_tag_returns_matching_models(vanilla_project):
    """search_entities with tag= filters to only models with that tag."""
    results = vanilla_project.search_entities('', tag='nonexistent_tag_xyz')
    assert results == []


def test_search_by_materialized_returns_matching(vanilla_project):
    """search_entities with materialized='view' returns models (most are views)."""
    results = vanilla_project.search_entities('', materialized='view')
    # Not asserting count — just that it works without error
    assert isinstance(results, list)
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_project_methods.py::test_model_tags_empty_by_default -v
```
Expected: FAIL — `AttributeError: 'DbtModel' object has no attribute 'tags'`

- [ ] **Step 3: Add `tags` and `materialized` to DbtModel**

In `src/dbt_tui/backend/model.py`, add after the `name` property:

```python
@property
def tags(self) -> list[str]:
    """Return tags from config(tags=[...]) or config(tags='single')."""
    calls = self._find_calls('config')
    if not calls:
        return []
    config: Call = calls[0]
    kwargs = {item.key: item.value for item in config.kwargs}
    tag_node = kwargs.get('tags')
    if tag_node is None:
        return []
    # tags can be a string or a list
    from jinja2.nodes import List as JinjaList, Const as JinjaConst
    if isinstance(tag_node, JinjaList):
        return [item.value for item in tag_node.items if isinstance(item, JinjaConst)]
    if isinstance(tag_node, JinjaConst):
        return [tag_node.value]
    return []

@property
def materialized(self) -> str:
    """Return materialization from config(materialized=...), default 'view'."""
    calls = self._find_calls('config')
    if not calls:
        return 'view'
    config: Call = calls[0]
    kwargs = {item.key: item.value for item in config.kwargs}
    mat_node = kwargs.get('materialized')
    if mat_node is None:
        return 'view'
    return str(mat_node.value)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_project_methods.py -v
```
Expected: tag/materialized tests now pass; fix any others that break.

---

### Task 2: Backend — filter params on `search_entities`

**Files:**
- Modify: `src/dbt_tui/backend/project.py`
- Modify: `src/dbt_tui/common/project.py`

- [ ] **Step 1: Update abstract signature**

In `src/dbt_tui/common/project.py`, find `search_entities` abstract method and update signature to:

```python
@abstractmethod
def search_entities(
    self,
    query: str,
    entity_type: str | None = None,
    tag: str | None = None,
    materialized: str | None = None,
) -> list['DbtEntityAbstract']:
    ...
```

- [ ] **Step 2: Update concrete implementation in project.py**

Find `search_entities` in `src/dbt_tui/backend/project.py` and add the two new parameters plus filtering logic after the existing entity_type filter:

```python
def search_entities(
    self,
    query: str,
    entity_type: str | None = None,
    tag: str | None = None,
    materialized: str | None = None,
) -> list[DbtEntityAbstract]:
    # ... existing logic for building candidates and scoring ...
    # After scoring/sorting, apply additional filters:
    if tag:
        from .model import DbtModel as _DM
        candidates = [
            e for e in candidates
            if isinstance(e, _DM) and tag in e.tags
        ]
    if materialized:
        from .model import DbtModel as _DM
        candidates = [
            e for e in candidates
            if isinstance(e, _DM) and e.materialized == materialized
        ]
    return candidates
```

**Important:** read the full `search_entities` method first before editing to understand where to insert the filter — add it at the end, after sorting, before the return.

- [ ] **Step 3: Run tests**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 4: Commit backend**

```bash
git add src/dbt_tui/backend/model.py src/dbt_tui/backend/project.py src/dbt_tui/common/project.py tests/test_project_methods.py
git commit -m "feat(search): add tags/materialized properties to DbtModel, filter params to search_entities"
```

---

### Task 3: Frontend — tag input and materialization select

**Files:**
- Modify: `src/dbt_tui/frontend/model_search/model_search.py`
- Modify: `src/dbt_tui/frontend/model_search/model_search_input.py`

- [ ] **Step 1: Add filter row to ModelSearch**

In `model_search.py`, add to the `compose` method — after the existing `Horizontal` with checkboxes, add a second filter row:

```python
yield containers.Horizontal(
    widgets.Label('Tag: '),
    widgets.Input(id='filter-tag', placeholder='tag name', classes='filter-input'),
    widgets.Label('Mat.: '),
    widgets.Select(
        options=[
            ('any', ''),
            ('view', 'view'),
            ('table', 'table'),
            ('incremental', 'incremental'),
            ('ephemeral', 'ephemeral'),
        ],
        id='filter-mat',
        value='',
    ),
    id='search-filters-2'
)
```

Add handler to re-run search when tag input changes:

```python
def on_input_changed(self, event: widgets.Input.Changed) -> None:
    if event.input.id == 'filter-tag':
        try:
            search_input = self.get_widget_by_id('search_input')
            if isinstance(search_input, ModelSearchInput):
                search_input._do_search(search_input.value)
        except Exception:
            pass

def on_select_changed(self, event: widgets.Select.Changed) -> None:
    if event.select.id == 'filter-mat':
        try:
            search_input = self.get_widget_by_id('search_input')
            if isinstance(search_input, ModelSearchInput):
                search_input._do_search(search_input.value)
        except Exception:
            pass
```

- [ ] **Step 2: Read tag/mat filters in `_do_search`**

In `model_search_input.py`, extend `_do_search` to read the new filters:

```python
# After reading want_models and want_macros, add:
try:
    tag_input = self.screen.get_widget_by_id('filter-tag')
    tag = tag_input.value.strip() if hasattr(tag_input, 'value') else None
    tag = tag or None  # empty string → None
except Exception:
    tag = None

try:
    from textual.widgets import Select
    mat_select = self.screen.get_widget_by_id('filter-mat')
    mat = mat_select.value if isinstance(mat_select, Select) else None
    mat = mat or None  # empty string → None
except Exception:
    mat = None

# Then pass to search_entities:
entities = self.app.project.search_entities(value, entity_type=entity_type, tag=tag, materialized=mat)
```

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/dbt_tui/frontend/model_search/model_search.py \
        src/dbt_tui/frontend/model_search/model_search_input.py
git commit -m "feat(model-search): add tag and materialization filters"
```
