from dbt_tui.backend.impact import analyze_impact, ImpactResult


def test_impact_result_dataclass():
    r = ImpactResult(total_affected=0, by_depth={}, all_affected=[])
    assert r.total_affected == 0


def test_analyze_impact_returns_result(dbt_project):
    model = dbt_project.models[0]
    result = analyze_impact(dbt_project, model)
    assert isinstance(result, ImpactResult)
    assert isinstance(result.total_affected, int)
    assert isinstance(result.all_affected, list)


def test_analyze_impact_finds_children(dbt_project):
    """Models with children should have non-empty impact."""
    for m in dbt_project.models:
        children = list(dbt_project.graph.successors(m))
        if children:
            result = analyze_impact(dbt_project, m)
            assert result.total_affected > 0
            break
