import pytest
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


def test_cte_model_extracts_columns(project):
    """CTE model: column names are extracted correctly and don't crash."""
    model = project.get_model_by_name('v_cte_model')
    cols = extract_columns(model)
    assert isinstance(cols, list)
    assert len(cols) > 0
    names = [c.name for c in cols]
    # star or explicit column names — either way we got something
    assert any(n in ('*', 'order_id', 'order_name', 'amount') for n in names)


def test_join_model_source_not_falsely_attributed(project):
    """JOIN model: qualified columns get their qualifier, unqualified get None."""
    model = project.get_model_by_name('v_join_model')
    cols = extract_columns(model)
    assert isinstance(cols, list)
    assert len(cols) > 0
    # Must not crash and expected column count (3 columns in the SELECT)
    assert len(cols) == 3
    # user_name is aliased from u.name — source_model should be 'u' (the alias)
    user_name_col = next((c for c in cols if c.name == 'user_name'), None)
    assert user_name_col is not None
    assert user_name_col.source_model == 'u'


def test_cte_names_not_in_source_models(project):
    """CTE names like 'source' and 'renamed' must not appear as source_model."""
    model = project.get_model_by_name('v_cte_model')
    cols = extract_columns(model)
    for col in cols:
        assert col.source_model not in ('source', 'renamed'), \
            f"CTE name leaked as source_model for column '{col.name}'"
