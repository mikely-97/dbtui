"""
Tests for macro loading and dependency tracking.

Covers:
- DbtMacro attributes (name, text, entity_type, file paths)
- macro-paths parsing from dbt_project.yml
- macro_calls detection on DbtModel
- macro→model edges in the dependency graph
- macro appearing in model.parents / model.children
"""
from pathlib import Path

import pytest

from dbt_tui.backend import DbtProject
from dbt_tui.backend.macro import DbtMacro


@pytest.fixture(scope="module")
def project():
    return DbtProject('tests/testing')


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

class TestMacroLoading:

    def test_macros_are_loaded(self, project):
        assert len(project.macros) >= 2

    def test_macros_by_name_populated(self, project):
        assert 'clean_string' in project.macros_by_name
        assert 'format_date' in project.macros_by_name

    def test_unused_macro_still_loaded(self, project):
        """format_date is not called by any model but should still be loaded."""
        assert 'format_date' in project.macros_by_name

    def test_macro_instance_type(self, project):
        assert isinstance(project.macros_by_name['clean_string'], DbtMacro)


# ---------------------------------------------------------------------------
# DbtMacro attributes
# ---------------------------------------------------------------------------

class TestMacroAttributes:

    def test_entity_type(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro.entity_type == 'macro'

    def test_name(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro.name == 'clean_string'

    def test_text_readable(self, project):
        macro = project.macros_by_name['clean_string']
        assert 'macro clean_string' in macro.text

    def test_file_name(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro.file_name == 'clean_string.sql'

    def test_file_path_full_exists(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro.file_path_full.exists()

    def test_file_path_relative(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro.file_path_relative == Path('macros/clean_string.sql')

    def test_file_extension(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro.file_extension == '.sql'

    def test_parents_always_empty(self, project):
        """Macros have no incoming dependencies."""
        macro = project.macros_by_name['clean_string']
        assert list(macro.parents) == []


# ---------------------------------------------------------------------------
# macro_calls on DbtModel
# ---------------------------------------------------------------------------

class TestMacroCalls:

    def test_macro_call_detected(self, project):
        model = project.get_model_by_name('v_macro_user')
        assert 'clean_string' in model.macro_calls

    def test_ref_not_in_macro_calls(self, project):
        """ref() is a dbt builtin and must be excluded from macro_calls."""
        model = project.get_model_by_name('v_b')
        assert 'ref' not in model.macro_calls

    def test_config_not_in_macro_calls(self, project):
        """config() is a dbt builtin and must be excluded."""
        # c_a uses {{ config(...) }}; check it's not treated as a user macro
        model = project.get_model_by_name('v_b')
        assert 'config' not in model.macro_calls

    def test_no_macro_calls_pure_sql(self, project):
        """A model with only raw SQL should have an empty macro_calls list."""
        model = project.get_model_by_name('v_a')
        assert model.macro_calls == []

    def test_uncalled_macro_absent(self, project):
        """format_date is defined but not called by v_macro_user."""
        model = project.get_model_by_name('v_macro_user')
        assert 'format_date' not in model.macro_calls


# ---------------------------------------------------------------------------
# Graph edges
# ---------------------------------------------------------------------------

class TestMacroGraph:

    def test_macro_is_graph_node(self, project):
        macro = project.macros_by_name['clean_string']
        assert macro in project.graph.nodes

    def test_unused_macro_is_graph_node(self, project):
        """Even unused macros should be added as graph nodes."""
        macro = project.macros_by_name['format_date']
        assert macro in project.graph.nodes

    def test_macro_has_model_child(self, project):
        macro = project.macros_by_name['clean_string']
        child_names = [c.name for c in macro.children]
        assert 'v_macro_user' in child_names

    def test_unused_macro_has_no_children(self, project):
        macro = project.macros_by_name['format_date']
        assert list(macro.children) == []

    def test_model_parents_include_macro(self, project):
        model = project.get_model_by_name('v_macro_user')
        parent_names = [p.name for p in model.parents]
        assert 'clean_string' in parent_names

    def test_model_parent_entity_types(self, project):
        """Parents of v_macro_user should contain at least one macro."""
        model = project.get_model_by_name('v_macro_user')
        entity_types = {p.entity_type for p in model.parents}
        assert 'macro' in entity_types

    def test_pure_model_parents_no_macros(self, project):
        """v_b only refs v_a with no macro calls, so its parents are all models."""
        model = project.get_model_by_name('v_b')
        entity_types = {p.entity_type for p in model.parents}
        assert entity_types == {'model'}
