from dbt_tui.backend.staleness import check_staleness, StalenessInfo


def test_staleness_info_dataclass():
    info = StalenessInfo(is_stale=True, stale_parents=['parent'], model_mtime=1.0, latest_parent_mtime=2.0)
    assert info.is_stale
    assert info.stale_parents == ['parent']


def test_check_staleness_returns_info(dbt_project):
    model = dbt_project.models[0]
    result = check_staleness(dbt_project, model)
    assert isinstance(result, StalenessInfo)
    assert isinstance(result.is_stale, bool)
    assert isinstance(result.stale_parents, list)
