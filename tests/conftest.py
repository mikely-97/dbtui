"""Shared pytest fixtures for dbt-tui tests."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
import yaml

from dbt_tui.backend import DbtProject
from dbt_tui.common import DbtTuiCache


@pytest.fixture
def dbt_project():
    """Fixture that provides a DbtProject instance for testing."""
    return DbtProject('tests/testing')


@pytest.fixture
def empty_cache():
    """Fixture that mocks load_cache to return empty cache."""
    empty = DbtTuiCache(
        last_open_project_raw=None,
        last_active_model=None,
        external_editor_command='vi'
    )
    with patch('dbt_tui.frontend.main.load_cache', return_value=empty):
        yield empty


@pytest.fixture
def temp_schema_file():
    """Fixture that provides a temporary schema.yml file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump({
            'version': 2,
            'models': [
                {'name': 'existing_model', 'description': 'Test model'}
            ]
        }, f)
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def temp_sql_file():
    """Fixture that provides a temporary SQL model file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write("SELECT * FROM source_table")
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def temp_sql_file_with_config():
    """Fixture that provides a temporary SQL file with existing config."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write("{{ config(materialized='view') }}\nSELECT * FROM source_table")
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)
