"""Tests for dependency count badges and project stats."""

import pytest
from dbt_tui.backend import DbtProject


class TestProjectStats:
    """Tests for project statistics and entity counts."""

    @pytest.fixture
    def project(self):
        """Provide a DbtProject instance for testing."""
        return DbtProject('tests/testing')

    def test_project_stats_counts(self, project):
        """Project has countable entities."""
        assert len(project.models) > 0
        assert isinstance(project.macros, list)
        assert hasattr(project, 'seeds')
        assert isinstance(project.seeds, list)
        assert hasattr(project, 'snapshots')
        assert isinstance(project.snapshots, list)

    def test_model_has_parents_children(self, project):
        """Models can access parents and children via graph."""
        if project.models:
            model = project.models[0]
            # Should have parents and children properties
            assert hasattr(model, 'parents')
            assert hasattr(model, 'children')
            # Should be iterable
            parents = list(model.parents)
            children = list(model.children)
            assert isinstance(parents, list)
            assert isinstance(children, list)

    def test_model_has_project_reference(self, project):
        """Models have reference to project."""
        if project.models:
            model = project.models[0]
            assert hasattr(model, 'project')
            assert model.project is not None
            assert hasattr(model.project, 'graph')

    def test_graph_counts_match(self, project):
        """Graph has proper predecessors and successors counts."""
        if project.models:
            model = project.models[0]
            parents = list(model.project.graph.predecessors(model))
            children = list(model.project.graph.successors(model))
            # Parents and children should be lists (possibly empty)
            assert isinstance(parents, list)
            assert isinstance(children, list)
            # Verify counts match what parents/children properties return
            assert len(parents) == len(list(model.parents))
            assert len(children) == len(list(model.children))
