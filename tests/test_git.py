from pathlib import Path

import pytest

from dbt_tui.backend.git import GitFileStatus, get_git_blame, get_git_log, get_git_status


@pytest.fixture
def model_path():
    return Path('tests/testing/vanilla/stg/v_a.sql')

@pytest.mark.asyncio
async def test_get_git_status_returns_status(model_path):
    status = await get_git_status(model_path)
    assert isinstance(status, GitFileStatus)

@pytest.mark.asyncio
async def test_git_status_has_valid_state(model_path):
    status = await get_git_status(model_path)
    assert status.state in ('untracked', 'modified', 'staged', 'clean', 'unknown')

@pytest.mark.asyncio
async def test_get_git_log_returns_list(model_path):
    log = await get_git_log(model_path, n=5)
    assert isinstance(log, list)

@pytest.mark.asyncio
async def test_get_git_blame_returns_lines(model_path):
    lines = await get_git_blame(model_path)
    assert isinstance(lines, list)

@pytest.mark.asyncio
async def test_not_in_repo_returns_gracefully(tmp_path):
    f = tmp_path / 'test.sql'
    f.write_text('select 1')
    status = await get_git_status(f)
    assert status.state in ('unknown', 'untracked', 'clean')
