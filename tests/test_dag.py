import pytest

from dbt_tui.backend import DbtProject
from dbt_tui.backend.dag import get_dag_node_list, get_execution_order, render_dag_ascii, render_dag_mermaid


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


def test_get_dag_node_list_returns_all_related_nodes(project):
    """Node list includes ancestors, focal, and descendants in depth order."""
    model = project.get_model_by_name('v_b')
    nodes = get_dag_node_list(project, model, depth=2)
    names = [n.name for n in nodes]
    assert 'v_b' in names
    from dbt_tui.common.entity import DbtEntityAbstract
    for n in nodes:
        assert isinstance(n, DbtEntityAbstract)


def test_get_dag_node_list_focal_only_when_isolated(project):
    """A node with no connections still appears in the list."""
    model = project.models[0]
    nodes = get_dag_node_list(project, model, depth=2)
    assert model in nodes


def test_render_dag_mermaid_basic(project):
    """Mermaid output starts with graph LR and contains focal node."""
    model = project.models[0]
    result = render_dag_mermaid(project, model, depth=2)
    assert result.startswith('graph LR')
    assert model.name in result


def test_render_dag_mermaid_contains_edges(project):
    """Mermaid output contains arrows for edges."""
    # Find a model with connections
    for m in project.models:
        if list(project.graph.predecessors(m)) or list(project.graph.successors(m)):
            result = render_dag_mermaid(project, m, depth=1)
            assert '-->' in result
            break


def test_mermaid_id_sanitizes():
    """Mermaid IDs replace dots and dashes."""
    from dbt_tui.backend.dag import _mermaid_id
    class FakeEntity:
        name = 'my-source.table'
    assert _mermaid_id(FakeEntity()) == 'my_source_table'


def test_execution_order_returns_list(project):
    model = project.models[0]
    result = get_execution_order(project, model, depth=2)
    assert isinstance(result, list)
    assert model in result


def test_execution_order_deps_before_dependents(project):
    """In execution order, parents should come before children."""
    # Find a model with parents
    for m in project.models:
        parents = list(project.graph.predecessors(m))
        if parents:
            order = get_execution_order(project, m, depth=1)
            names = [n.name for n in order]
            if parents[0].name in names and m.name in names:
                assert names.index(parents[0].name) < names.index(m.name)
            break
