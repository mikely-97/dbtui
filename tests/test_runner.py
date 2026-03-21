import pytest
from pathlib import Path
from dbt_tui.backend.runner import DbtRunner, RunResult

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
