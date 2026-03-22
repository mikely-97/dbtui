from dbt_tui.backend.doc_export import export_model_markdown


def test_export_contains_model_name(dbt_project):
    model = dbt_project.models[0]
    md = export_model_markdown(dbt_project, model)
    assert f'# {model.name}' in md


def test_export_contains_sql(dbt_project):
    model = dbt_project.models[0]
    md = export_model_markdown(dbt_project, model)
    assert '```sql' in md


def test_export_contains_metadata(dbt_project):
    model = dbt_project.models[0]
    md = export_model_markdown(dbt_project, model)
    assert '## Metadata' in md
    assert 'File:' in md
