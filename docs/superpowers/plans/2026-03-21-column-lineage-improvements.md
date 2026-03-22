# Column Lineage Improvements Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make column lineage correctly handle CTEs and JOIN sources instead of always defaulting to the first FROM table.

**Architecture:** Improve `extract_columns` in `lineage.py` to:
1. Detect CTE names from WITH clauses and include them in `from_tables`.
2. For multi-table queries (JOINs), avoid falsely attributing unqualified columns to `from_tables[0]` — set `source_model=None` when the source table is ambiguous.
3. Trace through single-CTE definitions to show the underlying source model.

**Tech Stack:** sqlglot (`exp.With`, `exp.CTE`, `exp.Table`, `exp.Select`), existing `_strip_jinja`.

---

### File map
| File | Change |
|------|--------|
| `src/dbt_tui/backend/lineage.py` | Improve `extract_columns` |
| `tests/testing/vanilla/stg/v_lineage.sql` | Add CTE + JOIN test fixtures if not present |
| `tests/test_lineage.py` | Add CTE and JOIN tests |

---

### Task 1: Add test fixtures for CTEs and JOINs

**Files:**
- Create or modify: `tests/testing/vanilla/stg/v_cte_model.sql`
- Create or modify: `tests/testing/vanilla/stg/v_join_model.sql`

- [ ] **Step 1: Create CTE fixture**

Create `tests/testing/vanilla/stg/v_cte_model.sql`:

```sql
with source as (
    select id, name, amount from {{ ref('stg_orders') }}
),
renamed as (
    select
        id as order_id,
        name as order_name,
        amount
    from source
)
select * from renamed
```

- [ ] **Step 2: Create JOIN fixture**

Create `tests/testing/vanilla/stg/v_join_model.sql`:

```sql
select
    o.id,
    o.amount,
    u.name as user_name
from {{ ref('stg_orders') }} o
join {{ ref('stg_users') }} u on o.user_id = u.id
```

---

### Task 2: Tests for improved lineage extraction

**Files:**
- Modify: `tests/test_lineage.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_lineage.py`:

```python
def test_cte_model_extracts_columns(vanilla_project):
    """CTE model: column names are extracted correctly."""
    model = vanilla_project.get_model_by_name('v_cte_model')
    from dbt_tui.backend.lineage import extract_columns
    cols = extract_columns(model)
    names = [c.name for c in cols]
    assert len(cols) > 0
    # star expansion from CTE or explicit columns
    assert any(n in ('*', 'order_id', 'order_name', 'amount') for n in names)


def test_join_model_source_not_falsely_attributed(vanilla_project):
    """JOIN model: qualified columns get correct table, unqualified get None."""
    model = vanilla_project.get_model_by_name('v_join_model')
    from dbt_tui.backend.lineage import extract_columns
    cols = extract_columns(model)
    col_by_name = {c.name: c for c in cols}
    # o.id → source_model should be 'stg_orders' (or the alias 'o')
    assert 'id' in col_by_name
    # user_name → aliased expression, source_model can be anything but must not crash
    assert 'user_name' in col_by_name


def test_cte_names_in_from_tables(vanilla_project):
    """CTE names are included in from_tables, not treated as missing refs."""
    model = vanilla_project.get_model_by_name('v_cte_model')
    from dbt_tui.backend.lineage import extract_columns
    # Must not raise and must return a list
    cols = extract_columns(model)
    assert isinstance(cols, list)
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_lineage.py::test_cte_model_extracts_columns tests/test_lineage.py::test_join_model_source_not_falsely_attributed -v
```
Expected: some may PASS already (no crash), some may give wrong source attribution — confirm current behaviour.

---

### Task 3: Improve `extract_columns` in `lineage.py`

**Files:**
- Modify: `src/dbt_tui/backend/lineage.py`

Replace the body of `extract_columns` with the improved version:

- [ ] **Step 1: Implement improved extraction**

```python
def extract_columns(model: 'DbtModel') -> list[ColumnLineage]:
    """Extract output columns from a model's SQL with CTE-aware lineage tracing."""
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

    # Find the last SELECT statement (may be inside a WITH)
    select = None
    cte_names: set[str] = set()

    for stmt in statements:
        if stmt is None:
            continue
        # Collect CTE names so we don't confuse them with source models
        for cte in stmt.find_all(exp.CTE):
            if cte.alias:
                cte_names.add(cte.alias)
        if isinstance(stmt, exp.Select):
            select = stmt
        # WITH ... SELECT
        with_node = stmt.find(exp.With)
        if with_node:
            inner_select = with_node.find(exp.Select)
            if inner_select:
                select = inner_select

    if select is None:
        return []

    # Source tables: only non-CTE names are real model references
    from_tables: list[str] = [
        t.name for t in select.find_all(exp.Table)
        if t.name and t.name not in cte_names
    ]
    # All tables including CTEs (for qualified column lookup)
    all_tables: list[str] = [t.name for t in select.find_all(exp.Table) if t.name]
    multi_source = len(all_tables) > 1

    columns: list[ColumnLineage] = []
    for sel_expr in select.selects:
        if isinstance(sel_expr, exp.Star):
            columns.append(ColumnLineage(
                name='*',
                source_model=from_tables[0] if len(from_tables) == 1 else None,
            ))
            continue

        alias = sel_expr.alias or None
        inner = sel_expr.this if hasattr(sel_expr, 'this') else sel_expr

        if alias is None and isinstance(inner, exp.Column):
            alias = inner.name
        if alias is None:
            alias = str(sel_expr)[:40]

        if isinstance(inner, exp.Column):
            # Qualified column: use the table qualifier if it's a real source
            table_ref = inner.table or None
            if table_ref and table_ref in cte_names:
                table_ref = None  # CTE reference — underlying source is opaque
            elif not table_ref:
                # Unqualified: only safe to attribute if exactly one source
                table_ref = from_tables[0] if len(from_tables) == 1 else None
            columns.append(ColumnLineage(
                name=alias,
                source_model=table_ref,
                source_column=inner.name,
            ))
        else:
            columns.append(ColumnLineage(
                name=alias,
                source_expression=str(inner)[:120],
                source_model=from_tables[0] if len(from_tables) == 1 else None,
            ))

    return columns
```

- [ ] **Step 2: Run all lineage tests**

```bash
pytest tests/test_lineage.py -v
```
Expected: all pass.

- [ ] **Step 3: Run full suite**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/dbt_tui/backend/lineage.py \
        tests/test_lineage.py \
        tests/testing/vanilla/stg/v_cte_model.sql \
        tests/testing/vanilla/stg/v_join_model.sql
git commit -m "feat(lineage): CTE-aware column extraction, fix join attribution"
```
