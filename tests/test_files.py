from dbt_tui.backend import DbtProject, DbtModelNotFoundException
from pytest import raises

# test that all models from all folders are visible
def test_all_models_are_visible():
    all_models = set(
        [
            'c_a.sql',
            'c_b.sql',
            'c_c1.sql',
            'c_c2.sql',
            'c_d.sql',
            'v_a.sql',
            'v_b.sql',
            'v_c1.sql',
            'v_c2.sql',
            'v_d.sql',
            'v_macro_user.sql',
            'v_lineage.sql',
            'v_cte_model.sql',
            'v_join_model.sql',
            'v_source_model.sql',
            'stg_users.sql',
            'i_d.sql',
            'i_a.sql',
            'i_c1.sql',
            'i_c2.sql',
            'i_b.sql',
        ]
    )
    dbt_project = DbtProject('tests/testing')
    model_filenames = [i.file_name for i in dbt_project.models]
    assert set(model_filenames) == all_models

# test that the v_a.sql has the same name as its filename
def test_model_name_is_file_name_by_default():
    dbt_project = DbtProject('tests/testing')
    assert dbt_project.get_model_by_file_name('v_a.sql').name == 'v_a'

# test that the c_a.sql has another name
def test_model_name_is_changed_by_config():
    dbt_project = DbtProject('tests/testing')
    assert dbt_project.get_model_by_file_name('c_a.sql').name == 'c_changed_name'

def test_not_found_by_name():
    dbt_project = DbtProject('tests/testing')
    with raises(DbtModelNotFoundException):
        dbt_project.get_model_by_name('this_model_does_not_exist')

def test_not_found_by_file_name():
    dbt_project = DbtProject('tests/testing')
    with raises(DbtModelNotFoundException):
        dbt_project.get_model_by_file_name('this_model_does_not_exist.sql')


def test_model_history_tracking():
    """Model history is maintained in the app."""
    from dbt_tui.frontend.main import DbtTuiFrontend
    app = DbtTuiFrontend()
    assert hasattr(app, '_model_history')
    assert isinstance(app._model_history, list)
    assert hasattr(app, '_MAX_HISTORY')
    assert app._MAX_HISTORY == 20

