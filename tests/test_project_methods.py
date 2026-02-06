from pathlib import Path
import shutil
import tempfile
from dbt_tui.backend import DbtProject, DbtModelNotFoundException
from dbt_tui.common import IncorrectFileExtensionException
from pytest import LogCaptureFixture, raises


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
