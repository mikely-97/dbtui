import pytest
from pathlib import Path
from dbt_tui.backend.runner import DbtRunner, RunResult
from dbt_tui.frontend.model_view.test_panel import parse_test_results, TestResult

@pytest.fixture
def project_path():
    return Path('tests/testing')

@pytest.mark.asyncio
async def test_runner_returns_run_result(project_path):
    runner = DbtRunner(project_path)
    result = await runner.run('--version')
    assert isinstance(result, RunResult)

@pytest.mark.asyncio
async def test_run_result_has_returncode(project_path):
    runner = DbtRunner(project_path)
    result = await runner.run('--version')
    assert isinstance(result.returncode, int)

@pytest.mark.asyncio
async def test_run_result_has_lines(project_path):
    runner = DbtRunner(project_path)
    result = await runner.run('--version')
    assert isinstance(result.lines, list)

@pytest.mark.asyncio
async def test_on_line_callback_called(project_path):
    runner = DbtRunner(project_path)
    collected = []
    await runner.run('--version', on_line=collected.append)
    assert len(collected) > 0

@pytest.mark.asyncio
async def test_success_property(project_path):
    runner = DbtRunner(project_path)
    result = await runner.run('--version')
    assert result.success == (result.returncode == 0)

@pytest.mark.asyncio
async def test_dbt_not_found_returns_result():
    """If dbt is not installed, returns a RunResult with error message."""
    runner = DbtRunner('/tmp')
    import unittest.mock as mock
    with mock.patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError):
        result = await runner.run('run')
    assert isinstance(result, RunResult)
    assert result.returncode == 1
    assert len(result.lines) > 0


def test_parse_passing_test():
    lines = [
        "Running with dbt=1.8.0",
        "  PASS test_not_null_stg_orders_id .......... [PASS in 0.14s]",
        "Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].name == 'test_not_null_stg_orders_id'
    assert results[0].status == 'PASS'


def test_parse_failing_test():
    lines = [
        "  FAIL 1 test_unique_stg_orders_id ......... [FAIL in 0.08s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].name == 'test_unique_stg_orders_id'
    assert results[0].status == 'FAIL'


def test_parse_warn_test():
    lines = [
        "  WARN 2 test_accepted_values_status ...... [WARN in 0.21s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].status == 'WARN'


def test_parse_error_test():
    lines = [
        "  ERROR test_schema_matches ............ [ERROR in 0.3s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].name == 'test_schema_matches'
    assert results[0].status == 'ERROR'


def test_parse_empty_output():
    results = parse_test_results([])
    assert results == []


def test_parse_mixed_output():
    lines = [
        "  PASS test_a ......... [PASS in 0.1s]",
        "  FAIL 1 test_b ....... [FAIL in 0.2s]",
        "  PASS test_c ......... [PASS in 0.1s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 3
    statuses = {r.name: r.status for r in results}
    assert statuses['test_a'] == 'PASS'
    assert statuses['test_b'] == 'FAIL'
    assert statuses['test_c'] == 'PASS'
