"""Tests for run_results.json parsing."""
import json
from pathlib import Path
from dbt_tui.backend.run_results import parse_run_results, get_model_run_result, ModelRunResult


def test_parse_missing_file(tmp_path):
    """Missing run_results.json returns empty dict."""
    assert parse_run_results(tmp_path) == {}


def test_parse_valid_results(tmp_path):
    """Valid run_results.json is parsed correctly."""
    target = tmp_path / 'target'
    target.mkdir()
    data = {
        'results': [
            {
                'unique_id': 'model.my_project.stg_orders',
                'status': 'pass',
                'execution_time': 1.23,
                'message': 'OK',
                'adapter_response': {'rows_affected': 100},
            }
        ]
    }
    (target / 'run_results.json').write_text(json.dumps(data))
    results = parse_run_results(tmp_path)
    assert 'stg_orders' in results
    assert results['stg_orders'].status == 'pass'
    assert results['stg_orders'].execution_time == 1.23


def test_get_model_run_result_missing(tmp_path):
    """Missing model returns None."""
    result = get_model_run_result(tmp_path, 'nonexistent')
    assert result is None


def test_parse_corrupt_json(tmp_path):
    """Corrupt JSON returns empty dict."""
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'run_results.json').write_text('not json!')
    assert parse_run_results(tmp_path) == {}


def test_model_run_result_dataclass():
    r = ModelRunResult(unique_id='model.p.m', status='pass', execution_time=0.5, message='OK', adapter_response='{}')
    assert r.status == 'pass'
