from dbt_tui.common.cache import DbtTuiCache, WorkspaceEntry, load_cache, save_cache


def test_workspace_entry_has_fields():
    w = WorkspaceEntry(project_path='/some/path', last_model='my_model')
    assert w.project_path == '/some/path'
    assert w.last_model == 'my_model'

def test_workspace_entry_optional_model():
    w = WorkspaceEntry(project_path='/some/path')
    assert w.last_model is None

def test_cache_has_workspaces_field():
    cache = DbtTuiCache()
    assert hasattr(cache, 'workspaces')
    assert isinstance(cache.workspaces, list)

def test_empty_cache_has_empty_workspaces():
    cache = DbtTuiCache()
    assert cache.workspaces == []

def test_workspace_roundtrip(tmp_path, monkeypatch):
    cache_file = tmp_path / 'cache.json'
    monkeypatch.setattr('dbt_tui.common.cache.ensure_cache_path', lambda: cache_file)
    cache = DbtTuiCache(
        workspaces=[
            WorkspaceEntry(project_path='/a/project', last_model='my_model'),
            WorkspaceEntry(project_path='/b/project', last_model=None),
        ]
    )
    save_cache(cache)
    loaded = load_cache()
    assert len(loaded.workspaces) == 2
    assert loaded.workspaces[0].project_path == '/a/project'
    assert loaded.workspaces[0].last_model == 'my_model'
    assert loaded.workspaces[1].last_model is None
