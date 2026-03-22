import pytest

from dbt_tui.backend import DbtProject
from dbt_tui.backend.docs import ModelDocs, collect_docs


@pytest.fixture(scope='module')
def project():
    return DbtProject('tests/testing')

def test_collect_docs_returns_model_docs(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    assert isinstance(docs, ModelDocs)

def test_description_is_string(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
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

def test_to_markdown_returns_string(project):
    model = project.get_model_by_name('v_a')
    docs = collect_docs(model)
    md = docs.to_markdown()
    assert isinstance(md, str)
    assert len(md) > 0

def test_no_doc_returns_placeholder(project):
    """Model with no schema.yml entries returns placeholder."""
    _ = project.get_model_by_name('v_a')
    docs = ModelDocs()  # empty
    assert docs.to_markdown() == '*No documentation available.*'
