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
