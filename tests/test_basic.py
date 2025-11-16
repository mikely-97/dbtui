from src.backend import DbtProject


# test that we can open a valid project
def test_open_correct_folder():
    assert DbtProject('tests/testing').dbt_project_yml['name'] == 'testing'


# test that an incorrect folder not opens
def test_open_nonexistent_folder():
    try:
        DbtProject('tests/nonexistent')
        raise Exception("Doesn't fail when opening a nonexistent folder")
    except FileNotFoundError as e:
        if e.args[0].startswith('Folder not found'):
            return 
        elif e.args[0].startswith('File not found'):
            raise Exception("Opens a nonexistent folder and can't find the dbt_project in it")
        else:
            raise e
    except e:
        raise e

# test that a correct folder with incorrect dbt_project doesn't open
def test_open_empty_folder():
    try:
        DbtProject('tests/empty')
        raise Exception("Doesn't fail when opening an empty folder")
    except FileNotFoundError as e:
        if e.args[0].startswith('Folder not found'):
            raise Exception("Can't open an empty folder with no dbt_project") 
        elif e.args[0].startswith('dbt folder is present, but dbt_project.yml is not found'):
            pass
        else:
            raise e
    except e:
        raise e

