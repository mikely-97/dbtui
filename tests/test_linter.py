from dbt_tui.backend.linter import lint_sql, LintIssue, _lint_with_sqlglot


def test_lint_sql_returns_list():
    result = lint_sql('SELECT 1')
    assert isinstance(result, list)


def test_lint_detects_select_star():
    result = _lint_with_sqlglot('SELECT * FROM users', 'duckdb')
    codes = [i.code for i in result]
    assert 'L044' in codes


def test_lint_clean_sql_no_star():
    result = _lint_with_sqlglot('SELECT id, name FROM users', 'duckdb')
    star_issues = [i for i in result if i.code == 'L044']
    assert len(star_issues) == 0


def test_lint_parse_error():
    result = _lint_with_sqlglot('SELEC BROKEN SQL !!!', 'duckdb')
    errors = [i for i in result if i.severity == 'error']
    assert len(errors) > 0


def test_lint_issue_dataclass():
    issue = LintIssue(line=1, col=5, code='L001', message='test')
    assert issue.severity == 'warning'


def test_lint_empty_sql():
    result = lint_sql('')
    assert isinstance(result, list)
