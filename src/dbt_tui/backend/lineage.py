"""Column-level lineage extraction using sqlglot."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from dbt_tui.backend.model import DbtModel


@dataclass
class ColumnLineage:
    name: str
    source_model: str | None = None
    source_column: str | None = None
    source_expression: str | None = None


def _strip_jinja(sql: str) -> str:
    """Replace Jinja blocks with plain SQL so sqlglot can parse."""
    sql = re.sub(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", r'\1', sql)
    sql = re.sub(r'\{\{[^}]+\}\}', 'placeholder', sql)
    sql = re.sub(r'\{%-?\s*.*?-?%\}', '', sql, flags=re.DOTALL)
    return sql


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
        # WITH ... SELECT: find the outermost SELECT inside the WITH block
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
            table_ref = inner.table or None
            if table_ref and table_ref in cte_names:
                table_ref = None  # CTE reference — underlying source is opaque
            elif not table_ref:
                # Unqualified: only attribute if exactly one real source
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
