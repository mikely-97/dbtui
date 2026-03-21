# Column-Level Lineage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse SQL SELECT statements to extract output column names and (where simple) trace each column back to its source model/column.

**Architecture:** Add `sqlglot` as a dependency. New `backend/lineage.py` with `extract_columns(model)` returning `list[ColumnLineage]`. A new `ColumnLineageView` screen shows a table of output columns with their source references. Simple aliased columns (`ref_col AS alias`) are fully traced; complex expressions show the expression text as source.

**Tech Stack:** `sqlglot` (SQL parser), Textual `DataTable`, existing `DbtModel`/`DbtProject`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | Modify | Add `sqlglot>=25.0` dependency |
| `src/dbt_tui/backend/lineage.py` | Create | `ColumnLineage` dataclass + `extract_columns()` |
| `src/dbt_tui/common/model.py` | Modify | Add abstract `columns` property |
| `src/dbt_tui/backend/model.py` | Modify | Implement `columns` property via `extract_columns` |
| `src/dbt_tui/frontend/lineage_view/__init__.py` | Create | Package marker |
| `src/dbt_tui/frontend/lineage_view/lineage_view.py` | Create | `ColumnLineageView(DbtTuiScreen)` |
| `src/dbt_tui/frontend/main.py` | Modify | Register screen; bind `L` key |
| `tests/test_lineage.py` | Create | Tests for column extraction |
| `tests/testing/vanilla/stg/v_a.sql` | Check | Ensure has a recognisable SELECT |

---

### Task 1: Add sqlglot dependency

- [ ] **Step 1: Add to pyproject.toml**

```toml
dependencies = [
    ...
    "sqlglot>=25.0",
]
```

- [ ] **Step 2: Install**

```bash
pip install sqlglot
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add sqlglot for SQL parsing"
```

---

### Task 2: Column lineage extractor

**Files:**
- Create: `src/dbt_tui/backend/lineage.py`
- Test: `tests/test_lineage.py`

- [ ] **Step 1: Write failing tests**

First check what `tests/testing/vanilla/stg/v_a.sql` contains — it should be a simple SELECT. If it isn't, add a test fixture model `tests/testing/vanilla/stg/v_lineage.sql`:

```sql
select
    id,
    upper(name) as name_upper,
    email
from {{ ref('v_a') }}
```

Create `tests/test_lineage.py`:
```python
import pytest
from pathlib import Path
from dbt_tui.backend import DbtProject
from dbt_tui.backend.lineage import extract_columns, ColumnLineage

@pytest.fixture(scope='module')
def project():
    return DbtProject('tests/testing')

def test_extract_columns_returns_list(project):
    model = project.get_model_by_name('v_lineage')
    cols = extract_columns(model)
    assert isinstance(cols, list)

def test_simple_column_detected(project):
    model = project.get_model_by_name('v_lineage')
    cols = extract_columns(model)
    names = [c.name for c in cols]
    assert 'id' in names

def test_alias_column_detected(project):
    model = project.get_model_by_name('v_lineage')
    cols = extract_columns(model)
    names = [c.name for c in cols]
    assert 'name_upper' in names

def test_column_source_model_tracked(project):
    model = project.get_model_by_name('v_lineage')
    cols = extract_columns(model)
    id_col = next(c for c in cols if c.name == 'id')
    assert id_col.source_model == 'v_a'

def test_expression_column_has_expression(project):
    model = project.get_model_by_name('v_lineage')
    cols = extract_columns(model)
    expr_col = next(c for c in cols if c.name == 'name_upper')
    assert expr_col.source_expression is not None

def test_column_lineage_type(project):
    model = project.get_model_by_name('v_lineage')
    cols = extract_columns(model)
    assert all(isinstance(c, ColumnLineage) for c in cols)
```

- [ ] **Step 2: Create the test fixture model**

Create `tests/testing/vanilla/stg/v_lineage.sql`:
```sql
select
    id,
    upper(name) as name_upper,
    email
from {{ ref('v_a') }}
```

Add to `tests/testing/vanilla/stg/schema.yml` under models list:
```yaml
  - name: v_lineage
    description: "Lineage test model"
```

- [ ] **Step 3: Run to verify failures**

```bash
pytest tests/test_lineage.py -x --tb=short -q
```

- [ ] **Step 4: Implement `extract_columns`**

Create `src/dbt_tui/backend/lineage.py`:
```python
"""Column-level lineage extraction using sqlglot."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from dbt_tui.backend.model import DbtModel


@dataclass
class ColumnLineage:
    name: str                          # output column name
    source_model: str | None = None    # ref'd model name if directly traced
    source_column: str | None = None   # source column name if directly traced
    source_expression: str | None = None  # raw expression if complex


def _strip_jinja(sql: str) -> str:
    """Replace Jinja blocks with placeholder SQL so sqlglot can parse."""
    # Replace {{ ref('x') }} with just the table name
    sql = re.sub(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", r'\1', sql)
    # Remove remaining {{ ... }} blocks
    sql = re.sub(r'\{\{[^}]+\}\}', 'placeholder', sql)
    # Remove {%- ... -%} blocks
    sql = re.sub(r'\{%-?\s*.*?-?%\}', '', sql, flags=re.DOTALL)
    return sql


def extract_columns(model: DbtModel) -> list[ColumnLineage]:
    """Extract output columns from a model's SQL, with simple lineage tracing."""
    try:
        import sqlglot
        import sqlglot.expressions as exp
    except ImportError:
        return []

    sql = _strip_jinja(model.text)

    try:
        statements = sqlglot.parse(sql, dialect='duckdb')
    except Exception:
        return []

    # Find the last SELECT statement
    select = None
    for stmt in statements:
        if isinstance(stmt, exp.Select):
            select = stmt
    if select is None:
        return []

    # Extract FROM clause to find source model
    from_tables: list[str] = []
    for table in select.find_all(exp.Table):
        from_tables.append(table.name)

    columns: list[ColumnLineage] = []
    for sel_expr in select.selects:
        if isinstance(sel_expr, exp.Star):
            columns.append(ColumnLineage(name='*', source_model=from_tables[0] if from_tables else None))
            continue

        alias = sel_expr.alias if sel_expr.alias else None
        inner = sel_expr.this if hasattr(sel_expr, 'this') else sel_expr

        if alias is None and isinstance(inner, exp.Column):
            alias = inner.name

        if alias is None:
            alias = str(sel_expr)[:40]

        # Simple column reference: col or table.col
        if isinstance(inner, exp.Column):
            source_col = inner.name
            source_tbl = inner.table or (from_tables[0] if from_tables else None)
            columns.append(ColumnLineage(
                name=alias,
                source_model=source_tbl,
                source_column=source_col,
            ))
        else:
            columns.append(ColumnLineage(
                name=alias,
                source_expression=str(inner)[:120],
                source_model=from_tables[0] if from_tables else None,
            ))

    return columns
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_lineage.py -x --tb=short -q
```

- [ ] **Step 6: Commit**

```bash
git add src/dbt_tui/backend/lineage.py tests/test_lineage.py \
        tests/testing/vanilla/stg/v_lineage.sql \
        tests/testing/vanilla/stg/schema.yml
git commit -m "feat: add column-level lineage extractor"
```

---

### Task 3: ColumnLineageView screen

**Files:**
- Create: `src/dbt_tui/frontend/lineage_view/__init__.py`
- Create: `src/dbt_tui/frontend/lineage_view/lineage_view.py`
- Modify: `src/dbt_tui/frontend/main.py`

- [ ] **Step 1: Create ColumnLineageView**

`src/dbt_tui/frontend/lineage_view/lineage_view.py`:
```python
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Footer
from textual.containers import Vertical
from textual.binding import Binding

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.lineage import extract_columns


class ColumnLineageView(DbtTuiScreen):
    BINDINGS = [Binding('escape', 'go_back', 'Back')]

    def compose(self) -> ComposeResult:
        yield Static('', id='lineage-header')
        yield DataTable(id='lineage-table')
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#lineage-table', DataTable)
        table.add_columns('Column', 'Source Model', 'Source Column', 'Expression')
        self._refresh()

    def on_model_change(self, model) -> None:
        self._refresh()

    def _refresh(self) -> None:
        model = self.app.model
        header = self.query_one('#lineage-header', Static)
        table = self.query_one('#lineage-table', DataTable)
        table.clear()

        if model is None:
            header.update('No model selected.')
            return

        header.update(f'Column lineage: [bold]{model.name}[/bold]')
        cols = extract_columns(model)

        if not cols:
            table.add_row('(no columns detected)', '', '', '')
            return

        for c in cols:
            table.add_row(
                c.name or '',
                c.source_model or '',
                c.source_column or '',
                c.source_expression or '',
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()
```

- [ ] **Step 2: Register in main.py**

```python
from dbt_tui.frontend.lineage_view.lineage_view import ColumnLineageView

# SCREENS:
'lineage_view': ColumnLineageView,

# BINDINGS:
Binding('l', 'push_screen("lineage_view")', 'Lineage'),
```

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 4: Commit**

```bash
git add src/dbt_tui/frontend/lineage_view/ src/dbt_tui/frontend/main.py
git commit -m "feat: add column lineage view screen (L key)"
```
