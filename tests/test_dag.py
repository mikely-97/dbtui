import pytest
from pathlib import Path
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
    model = project.get_model_by_name('v_b')
    output = render_dag_ascii(project, model, depth=2)
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
