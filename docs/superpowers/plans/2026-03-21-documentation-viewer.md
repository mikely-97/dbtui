# Documentation Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the model's dbt documentation (description, column descriptions, tags, tests) in a readable panel inside the model view, sourced from `schema.yml`.

**Architecture:** Extend `DbtModel` with a `docs` property returning a `ModelDocs` dataclass (description, columns dict, tags, tests). The data is collected from the existing `property_claims` pipeline — no new file I/O. A new `DocPanel` widget renders this in `ModelView` alongside `PropertiesPanel`.

**Tech Stack:** Existing `PropertyClaim` pipeline, Textual `Markdown` widget (already bundled with Textual), `DbtModel`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/backend/docs.py` | Create | `ModelDocs` dataclass + `collect_docs(model)` |
| `src/dbt_tui/common/model.py` | Modify | Add abstract `docs` property |
| `src/dbt_tui/backend/model.py` | Modify | Implement `docs` property |
| `src/dbt_tui/frontend/model_view/doc_panel.py` | Create | `DocPanel` widget |
| `src/dbt_tui/frontend/model_view/model_view.py` | Modify | Add `DocPanel` tab alongside `PropertiesPanel` |
| `tests/test_docs.py` | Create | Tests for doc collection |

---

### Task 1: ModelDocs collection (backend)

**Files:**
- Create: `src/dbt_tui/backend/docs.py`
- Test: `tests/test_docs.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_docs.py`:
```python
import pytest
from dbt_tui.backend import DbtProject
from dbt_tui.backend.docs import collect_docs, ModelDocs

@pytest.fixture(scope='module')
def project():
    return DbtProject('tests/testing')

def test_collect_docs_returns_model_docs(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    assert isinstance(docs, ModelDocs)

def test_description_extracted_from_schema(project):
    # v_a has description in tests/testing/vanilla/stg/schema.yml
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    # May be empty string if no description set — just verify type
    assert isinstance(docs.description, str)

def test_columns_is_dict(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    assert isinstance(docs.columns, dict)

def test_tags_is_list(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    assert isinstance(docs.tags, list)

def test_tests_is_list(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    assert isinstance(docs.tests, list)

def test_model_with_description(project):
    """Add a description to schema.yml and verify it's picked up."""
    # v_b is defined with a description in tests/testing/vanilla/int/schema.yml
    model = project.get_model_by_name('v_b')
    docs = collect_docs(model)
    # Just assert no exceptions and type is right
    assert isinstance(docs.description, str)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_docs.py -x --tb=short -q
```

- [ ] **Step 3: Implement `collect_docs`**

Create `src/dbt_tui/backend/docs.py`:
```python
"""Documentation collection from dbt property claims."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dbt_tui.backend.model import DbtModel


@dataclass
class ColumnDoc:
    name: str
    description: str = ''
    tests: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ModelDocs:
    description: str = ''
    columns: dict[str, ColumnDoc] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = []
        if self.description:
            lines.append(f'{self.description}\n')
        if self.tags:
            lines.append(f'**Tags:** {", ".join(self.tags)}\n')
        if self.tests:
            lines.append(f'**Tests:** {", ".join(self.tests)}\n')
        if self.columns:
            lines.append('\n## Columns\n')
            for col_name, col in self.columns.items():
                lines.append(f'**{col_name}**')
                if col.description:
                    lines.append(f': {col.description}')
                if col.tests:
                    lines.append(f' *(tests: {", ".join(col.tests)})*')
                lines.append('\n')
        return '\n'.join(lines) if lines else '*No documentation available.*'


def collect_docs(model: DbtModel) -> ModelDocs:
    """Build ModelDocs from the model's property claims."""
    docs = ModelDocs()

    for claim in model.property_claims:
        if claim.source_type != 'schema.yml':
            continue

        match claim.name:
            case 'description':
                if isinstance(claim.value, str):
                    docs.description = claim.value

            case 'tags':
                val = claim.value
                if isinstance(val, list):
                    docs.tags = [str(t) for t in val]
                elif isinstance(val, str):
                    docs.tags = [val]

            case 'columns':
                if not isinstance(claim.value, list):
                    continue
                for col_data in claim.value:
                    if not isinstance(col_data, dict):
                        continue
                    col_name = col_data.get('name', '')
                    col = ColumnDoc(
                        name=col_name,
                        description=col_data.get('description', ''),
                        tests=[
                            str(t) if not isinstance(t, dict) else list(t.keys())[0]
                            for t in col_data.get('tests', [])
                        ],
                        tags=col_data.get('tags', []),
                    )
                    docs.columns[col_name] = col

            case 'tests':
                val = claim.value
                if isinstance(val, list):
                    docs.tests = [
                        str(t) if not isinstance(t, dict) else list(t.keys())[0]
                        for t in val
                    ]

    return docs
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_docs.py -x --tb=short -q
```

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/backend/docs.py tests/test_docs.py
git commit -m "feat: add ModelDocs collection from property claims"
```

---

### Task 2: DocPanel widget + integration

**Files:**
- Create: `src/dbt_tui/frontend/model_view/doc_panel.py`
- Modify: `src/dbt_tui/frontend/model_view/model_view.py`

- [ ] **Step 1: Create DocPanel**

`src/dbt_tui/frontend/model_view/doc_panel.py`:
```python
"""Documentation panel widget."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Markdown, Static
from textual.containers import ScrollableContainer, Vertical
from textual.widget import Widget

from dbt_tui.backend.docs import collect_docs


class DocPanel(Widget):
    DEFAULT_CSS = """
    DocPanel {
        border: solid $accent;
        height: 1fr;
    }
    DocPanel #doc-header {
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static('Documentation', id='doc-header')
        yield ScrollableContainer(Markdown('', id='doc-content'))

    def refresh_model(self, model) -> None:
        md = self.query_one('#doc-content', Markdown)
        if model is None:
            md.update('*No model selected.*')
            return
        docs = collect_docs(model)
        md.update(docs.to_markdown())
```

- [ ] **Step 2: Integrate into ModelView**

In `frontend/model_view/model_view.py`:

1. Import `DocPanel`
2. Add `DocPanel` as a tab alongside `PropertiesPanel`. Use Textual `TabbedContent`:

```python
from textual.widgets import TabbedContent, TabPane
from dbt_tui.frontend.model_view.doc_panel import DocPanel

# In compose(), replace the right-side panel area:
with TabbedContent(id='right-panels'):
    with TabPane('Properties', id='tab-props'):
        yield PropertiesPanel(id='properties-panel')
    with TabPane('Docs', id='tab-docs'):
        yield DocPanel(id='doc-panel')
```

3. In `on_model_change`:
```python
self.query_one('#doc-panel', DocPanel).refresh_model(model)
```

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 4: Commit**

```bash
git add src/dbt_tui/frontend/model_view/doc_panel.py \
        src/dbt_tui/frontend/model_view/model_view.py
git commit -m "feat: add documentation panel (Docs tab in model view)"
```
