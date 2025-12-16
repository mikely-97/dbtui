from src.backend import DbtProject, DbtModelNotFoundException
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
