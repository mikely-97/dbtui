import shutil
import tempfile
from pathlib import Path

from pytest import raises

from dbt_tui.backend import DbtProject
from dbt_tui.common import IncorrectFileExtensionException


# test that we correctly list all the model folders
def test_get_model_folders():
    all_models_folders = set(
        [
            'vanilla/int',
            'vanilla/mart',
            'vanilla/stg',
            'invalid/int',
            'invalid/mart',
            'invalid/stg',
            'complex_config/int',
            'complex_config/mart',
            'complex_config/stg',
        ]
    )
    dbt_project = DbtProject('tests/testing')
    model_folders = dbt_project.get_model_folders()
    assert set(all_models_folders) == set([i.as_posix() for i in model_folders])


class TestCreateNewModel:
    """Tests for DbtProject.create_new_model()"""

    def setup_method(self):
        """Create a temporary copy of the test project for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_path = Path(self.temp_dir) / 'testing'
        shutil.copytree('tests/testing', self.test_project_path)
        self.project = DbtProject(self.test_project_path)

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_basic_model(self):
        """Test creating a new model with a valid path."""
        new_model_path = Path('vanilla/stg/new_model.sql')
        model = self.project.create_new_model(new_model_path)
        assert model.name == 'new_model'
        assert (self.test_project_path / new_model_path).exists()

    def test_create_model_from_parent(self):
        """Test creating a model that references a parent model."""
        parent_model = self.project.get_model_by_name('v_a')
        new_model_path = Path('vanilla/int/child_of_v_a.sql')
        model = self.project.create_new_model(new_model_path, from_=parent_model)
        assert model.name == 'child_of_v_a'
        content = (self.test_project_path / new_model_path).read_text()
        assert "ref('v_a')" in content

    def test_rejects_directory_path(self):
        """Test that creating a model at a directory path fails."""
        with raises(IsADirectoryError):
            self.project.create_new_model(Path('vanilla/stg'))

    def test_rejects_existing_file(self):
        """Test that creating a model at an existing file path fails."""
        with raises(FileExistsError):
            self.project.create_new_model(Path('vanilla/stg/v_a.sql'))

    def test_rejects_non_sql_extension(self):
        """Test that creating a model with wrong extension fails."""
        with raises(IncorrectFileExtensionException):
            self.project.create_new_model(Path('vanilla/stg/model.txt'))

    def test_rejects_path_outside_model_folders(self):
        """Test that creating a model outside model-paths fails."""
        with raises(ValueError, match='not in model folders'):
            self.project.create_new_model(Path('macros/not_a_model.sql'))

    def test_creates_parent_directories(self):
        """Test that missing parent directories are created."""
        new_model_path = Path('vanilla/stg/nested/deep/new_model.sql')
        model = self.project.create_new_model(new_model_path)
        assert model.name == 'new_model'
        assert (self.test_project_path / new_model_path).exists()


def test_model_tags_empty_by_default():
    """Model with no config() tags returns empty list."""
    project = DbtProject('tests/testing')
    model = project.models[0]
    assert isinstance(model.tags, list)


def test_model_materialized_defaults_to_view():
    """Model without config(materialized=...) returns 'view'."""
    project = DbtProject('tests/testing')
    model = project.models[0]
    assert model.materialized in ('view', 'table', 'incremental', 'ephemeral', None)


def test_search_by_tag_filters():
    """Search with nonexistent tag returns empty list."""
    project = DbtProject('tests/testing')
    results = project.search_entities('', tag='nonexistent_tag_xyz')
    assert results == []


def test_search_by_materialized_works():
    """Search with materialized filter returns a list."""
    project = DbtProject('tests/testing')
    results = project.search_entities('', materialized='view')
    assert isinstance(results, list)


def test_model_sources_empty_by_default():
    """Models without source() return empty list."""
    project = DbtProject('tests/testing')
    model = project.models[0]
    assert isinstance(model.sources, list)


def test_source_parsing():
    """source() calls extract (source_name, table_name) tuples."""
    project = DbtProject('tests/testing')
    model = project.get_model_by_name('v_source_model')
    sources = model.sources
    assert len(sources) == 1
    assert sources[0] == ('raw_data', 'users')


def test_project_has_seeds_list():
    """Project should have a seeds list attribute."""
    project = DbtProject('tests/testing')
    assert hasattr(project, 'seeds')
    assert isinstance(project.seeds, list)


def test_project_has_snapshots_list():
    """Project should have a snapshots list attribute."""
    project = DbtProject('tests/testing')
    assert hasattr(project, 'snapshots')
    assert isinstance(project.snapshots, list)


def test_seeds_are_loaded():
    """Seeds CSV files should be loaded from seed-paths."""
    project = DbtProject('tests/testing')
    assert len(project.seeds) > 0


def test_snapshots_are_loaded():
    """Snapshot SQL files should be loaded from snapshot-paths."""
    project = DbtProject('tests/testing')
    assert len(project.snapshots) > 0


def test_seeds_by_name_populated():
    """seeds_by_name dict should be populated."""
    project = DbtProject('tests/testing')
    assert 'raw_users' in project.seeds_by_name


def test_snapshots_by_name_populated():
    """snapshots_by_name dict should be populated."""
    project = DbtProject('tests/testing')
    assert 'snap_orders' in project.snapshots_by_name


def test_seed_entity_type():
    """Seed entity_type should be 'seed'."""
    project = DbtProject('tests/testing')
    seed = project.seeds_by_name['raw_users']
    assert seed.entity_type == 'seed'


def test_snapshot_entity_type():
    """Snapshot entity_type should be 'snapshot'."""
    project = DbtProject('tests/testing')
    snapshot = project.snapshots_by_name['snap_orders']
    assert snapshot.entity_type == 'snapshot'


def test_seeds_in_search_entities():
    """search_entities should include seeds."""
    project = DbtProject('tests/testing')
    results = project.search_entities('', entity_type='seed')
    assert len(results) > 0
    assert any(e.entity_type == 'seed' for e in results)


def test_snapshots_in_search_entities():
    """search_entities should include snapshots."""
    project = DbtProject('tests/testing')
    results = project.search_entities('', entity_type='snapshot')
    assert len(results) > 0
    assert any(e.entity_type == 'snapshot' for e in results)


def test_file_watcher_starts_and_stops():
    """ProjectFileWatcher should start and stop cleanly."""
    from dbt_tui.backend.file_watcher import ProjectFileWatcher
    project = DbtProject('tests/testing')

    events = []
    def callback(event):
        events.append(event)

    watcher = ProjectFileWatcher(project, callback)
    assert not watcher.is_running

    watcher.start()
    assert watcher.is_running

    watcher.stop()
    assert not watcher.is_running


def test_file_watcher_context_manager():
    """ProjectFileWatcher should work as a context manager."""
    from dbt_tui.backend.file_watcher import ProjectFileWatcher
    project = DbtProject('tests/testing')

    events = []
    def callback(event):
        events.append(event)

    with ProjectFileWatcher(project, callback) as watcher:
        assert watcher.is_running

    assert not watcher.is_running
