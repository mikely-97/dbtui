"""
Tests for model search functionality and cache operations.
"""

import json
from pathlib import Path

import pytest

from dbt_tui.backend import DbtProject
from dbt_tui.common import DbtTuiCache, load_cache, save_cache


class TestModelSearch:
    """Test model search functionality."""

    def test_search_by_exact_name(self, dbt_project):
        """Should find model by exact name match."""
        results = dbt_project.search_model('v_a')

        assert len(results) == 1
        assert results[0].name == 'v_a'

    def test_search_by_changed_name(self, dbt_project):
        """Should find model by its config-changed name."""
        results = dbt_project.search_model('c_changed_name')

        assert len(results) == 1
        assert results[0].name == 'c_changed_name'
        assert results[0].file_name == 'c_a.sql'  # Original filename

    def test_search_nonexistent_model(self, dbt_project):
        """Should return empty list for nonexistent model."""
        results = dbt_project.search_model('nonexistent_model')

        assert len(results) == 0

    def test_search_returns_model_instance(self, dbt_project):
        """Search results should be DbtModel instances."""
        results = dbt_project.search_model('v_a')

        assert len(results) == 1
        model = results[0]

        # Should have all expected attributes
        assert hasattr(model, 'name')
        assert hasattr(model, 'file_name')
        assert hasattr(model, 'file_path_full')
        assert hasattr(model, 'parents')
        assert hasattr(model, 'children')
        assert hasattr(model, 'refs')


class TestCacheOperations:
    """Test cache loading and saving operations."""

    def test_load_cache_creates_if_missing(self, tmp_path, monkeypatch):
        """Should create cache file if it doesn't exist."""
        # Mock the cache directory
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        cache = load_cache()

        # Should return a DbtTuiCache instance
        assert isinstance(cache, DbtTuiCache)

        # Cache file should be created
        cache_file = tmp_path / 'cache.json'
        assert cache_file.exists()

    def test_load_cache_with_clear_flag(self, tmp_path, monkeypatch):
        """Should clear cache when clear_cache=True."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        # Create cache with some data
        cache_file = tmp_path / 'cache.json'
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump({
                'last_open_project_raw': '/some/project',
                'last_active_model': 'some_model',
                'external_editor_command': 'vim'
            }, f)

        # Load with clear_cache=True
        cache = load_cache(clear_cache=True)

        # Should have default values
        assert cache.last_open_project is None
        assert cache.last_active_model is None
        assert cache.external_editor_command == 'vi'

    def test_save_and_load_cache(self, tmp_path, monkeypatch):
        """Should persist cache data correctly."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        project_path = Path('/test/project')
        model_name = 'test_model'
        editor_command = 'code'

        # Save cache
        save_cache(DbtTuiCache(
            last_open_project_raw=str(project_path),
            last_active_model=model_name,
            external_editor_command=editor_command,
        ))

        # Load cache
        cache = load_cache()

        # Should retrieve saved values
        assert cache.last_open_project == project_path
        assert cache.last_active_model == model_name
        assert cache.external_editor_command == editor_command

    def test_cache_handles_none_values(self, tmp_path, monkeypatch):
        """Should handle None values correctly."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        # Save with None values
        save_cache(DbtTuiCache(
            last_open_project_raw=None,
            last_active_model=None,
            external_editor_command='vi',
        ))

        # Load cache
        cache = load_cache()

        # Should handle None gracefully
        assert cache.last_open_project is None
        assert cache.last_active_model is None

    def test_cache_handles_invalid_json(self, tmp_path, monkeypatch):
        """Should recreate cache if JSON is invalid."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        # Create invalid JSON file
        cache_file = tmp_path / 'cache.json'
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            f.write('{ invalid json }')

        # Should not raise exception, should recreate cache
        cache = load_cache()

        assert isinstance(cache, DbtTuiCache)
        assert cache.last_open_project is None

    def test_cache_path_conversion(self):
        """Should convert between Path and string correctly."""
        cache = DbtTuiCache()

        # Test setting with Path
        test_path = Path('/test/project')
        cache.last_open_project = test_path
        assert cache.last_open_project == test_path
        assert cache.last_open_project_raw == str(test_path)

        # Test setting with string
        test_str = '/another/project'
        cache.last_open_project = test_str
        assert cache.last_open_project == Path(test_str)
        assert cache.last_open_project_raw == test_str

    def test_cache_bookmarks_round_trip(self, tmp_path, monkeypatch):
        """Bookmarks persist through save/load cycle."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        # Create and save cache with bookmarks
        cache = load_cache(clear_cache=True)
        cache.bookmarks = ['model_a', 'model_b']
        save_cache(cache)

        # Load and verify
        loaded = load_cache()
        assert loaded.bookmarks == ['model_a', 'model_b']

    def test_cache_bookmarks_empty_by_default(self, tmp_path, monkeypatch):
        """Bookmarks should be empty list by default."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        cache = load_cache(clear_cache=True)
        assert cache.bookmarks == []

    def test_cache_bookmarks_add_and_remove(self, tmp_path, monkeypatch):
        """Should handle adding and removing bookmarks."""
        monkeypatch.setattr('dbt_tui.common.cache.user_cache_dir', lambda x: str(tmp_path))

        cache = load_cache(clear_cache=True)

        # Add bookmarks
        cache.bookmarks.append('model_x')
        cache.bookmarks.append('model_y')
        save_cache(cache)

        # Verify
        loaded = load_cache()
        assert 'model_x' in loaded.bookmarks
        assert 'model_y' in loaded.bookmarks

        # Remove one
        loaded.bookmarks.remove('model_x')
        save_cache(loaded)

        # Verify removal
        loaded_again = load_cache()
        assert 'model_x' not in loaded_again.bookmarks
        assert 'model_y' in loaded_again.bookmarks


class TestModelFolderOperations:
    """Test operations related to model folders."""

    def test_get_model_folders(self, dbt_project):
        """Should return all folders containing models."""
        folders = dbt_project.get_model_folders()

        # Should be a list of Paths
        assert isinstance(folders, list)
        assert all(isinstance(f, Path) for f in folders)

        # Should have folders from all model paths
        folder_names = [str(f) for f in folders]

        # Check for expected folder structures
        assert any('stg' in name for name in folder_names)
        assert any('int' in name for name in folder_names)
        assert any('mart' in name for name in folder_names)

    def test_model_folders_are_sorted(self, dbt_project):
        """Model folders should be returned in sorted order."""
        folders = dbt_project.get_model_folders()

        folder_strings = [str(f) for f in folders]
        assert folder_strings == sorted(folder_strings)

    def test_model_folders_are_unique(self, dbt_project):
        """Should not have duplicate folders."""
        folders = dbt_project.get_model_folders()

        # Convert to set to check uniqueness
        assert len(folders) == len(set(str(f) for f in folders))


class TestProjectRefresh:
    """Test project refresh operations."""

    def test_project_refresh_reloads_models(self, dbt_project):
        """Refresh should reload all models."""
        initial_model_count = len(dbt_project.models)

        # Refresh the project
        dbt_project.refresh()

        # Should still have same number of models
        assert len(dbt_project.models) == initial_model_count

    def test_refresh_rebuilds_graph(self, dbt_project):
        """Refresh should rebuild the dependency graph."""
        dbt_project.refresh()

        # Graph should have nodes and edges
        assert dbt_project.graph.number_of_nodes() > 0
        assert dbt_project.graph.number_of_edges() > 0

    def test_refresh_updates_model_lookups(self, dbt_project):
        """Refresh should update the model lookup dictionaries."""
        dbt_project.refresh()

        # Should be able to lookup by name
        model_by_name = dbt_project.get_model_by_name('v_a')
        assert model_by_name is not None

        # Should be able to lookup by filename
        model_by_file = dbt_project.get_model_by_file_name('v_a.sql')
        assert model_by_file is not None

        # Should be the same model
        assert model_by_name == model_by_file


class TestModelRelationships:
    """Test model parent/child relationships."""

    def test_model_has_parents(self, dbt_project):
        """Models with refs should have parents."""
        model = dbt_project.get_model_by_name('v_b')

        # v_b references v_a
        parents = list(model.parents)
        assert len(parents) > 0

        # Should include v_a
        parent_names = [p.name for p in parents]
        assert 'v_a' in parent_names

    def test_model_has_children(self, dbt_project):
        """Models that are referenced should have children."""
        model = dbt_project.get_model_by_name('v_a')

        # v_a is referenced by v_b
        children = list(model.children)
        assert len(children) > 0

        # Should include v_b
        child_names = [c.name for c in children]
        assert 'v_b' in child_names

    def test_parents_and_children_are_sorted(self, dbt_project):
        """Parents and children lists should be sorted by name."""
        model = dbt_project.get_model_by_name('v_d')

        # Get parents
        parents = list(model.parents)
        if len(parents) > 1:
            parent_names = [p.name for p in parents]
            assert parent_names == sorted(parent_names)

        # Get children (if any)
        children = list(model.children)
        if len(children) > 1:
            child_names = [c.name for c in children]
            assert child_names == sorted(child_names)

    def test_model_refs_extraction(self, dbt_project):
        """Should correctly extract refs from model SQL."""
        model = dbt_project.get_model_by_name('v_b')

        refs = model.refs
        assert isinstance(refs, list)
        assert len(refs) > 0
        assert 'v_a' in refs


class TestSearchEntities:
    """Test search_entities with fuzzy scoring and filters."""

    @pytest.fixture
    def project(self):
        return DbtProject('tests/testing')

    def test_search_scores_exact_prefix_higher(self, project):
        """'v_a' should rank exact-prefix matches above partial matches."""
        results = project.search_entities('v_a', entity_type='model')
        names = [r.name for r in results]
        assert names[0] == 'v_a'

    def test_search_filters_by_entity_type_model(self, project):
        results = project.search_entities('clean', entity_type='macro')
        assert all(r.entity_type == 'macro' for r in results)
        assert any(r.name == 'clean_string' for r in results)

    def test_search_filters_by_entity_type_excludes_others(self, project):
        results = project.search_entities('v_a', entity_type='macro')
        assert all(r.entity_type == 'macro' for r in results)

    def test_search_path_prefix_filter(self, project):
        results = project.search_entities('', path_prefix='vanilla/stg')
        assert all('vanilla/stg' in str(r.file_path_relative) for r in results)

    def test_search_empty_query_returns_all(self, project):
        results = project.search_entities('')
        assert len(results) >= len(project.models)

    def test_search_returns_macros_when_no_filter(self, project):
        results = project.search_entities('clean_string')
        names = [r.name for r in results]
        assert 'clean_string' in names


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_model_with_no_refs(self, dbt_project):
        """Models without refs should have empty parents list."""
        model = dbt_project.get_model_by_name('v_a')

        # v_a is a staging model with no dependencies
        assert len(list(model.parents)) == 0

    def test_model_with_multiple_parents(self, dbt_project):
        """Models can have multiple parents."""
        model = dbt_project.get_model_by_name('v_d')

        # v_d depends on v_c1 and v_c2
        parents = list(model.parents)
        assert len(parents) >= 2

        parent_names = {p.name for p in parents}
        assert 'v_c1' in parent_names
        assert 'v_c2' in parent_names

    def test_model_text_property(self, dbt_project):
        """Should be able to read model text."""
        model = dbt_project.get_model_by_name('v_a')

        text = model.text
        assert isinstance(text, str)
        assert len(text) > 0

        # Should contain SQL keywords
        assert 'select' in text.lower()
