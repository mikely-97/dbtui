"""Tests for manifest.json parsing."""
import json
from dbt_tui.backend.manifest import parse_manifest, get_manifest_node, ManifestNode, ManifestColumn


def test_parse_missing_manifest(tmp_path):
    assert parse_manifest(tmp_path) == {}


def test_parse_valid_manifest(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    data = {
        'nodes': {
            'model.my_project.stg_orders': {
                'name': 'stg_orders',
                'resource_type': 'model',
                'description': 'Staged orders',
                'columns': {
                    'id': {'name': 'id', 'description': 'Order ID', 'data_type': 'integer'},
                    'amount': {'name': 'amount', 'description': '', 'data_type': 'numeric'},
                },
                'depends_on': {'nodes': ['model.my_project.raw_orders']},
                'config': {'materialized': 'view', 'tags': ['finance']},
                'compiled_code': 'SELECT id, amount FROM raw.orders',
            }
        }
    }
    (target / 'manifest.json').write_text(json.dumps(data))
    result = parse_manifest(tmp_path)
    assert 'stg_orders' in result
    node = result['stg_orders']
    assert node.description == 'Staged orders'
    assert len(node.columns) == 2
    assert node.materialized == 'view'
    assert node.compiled_code == 'SELECT id, amount FROM raw.orders'


def test_parse_corrupt_manifest(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'manifest.json').write_text('not json')
    assert parse_manifest(tmp_path) == {}


def test_get_manifest_node_missing(tmp_path):
    assert get_manifest_node(tmp_path, 'nonexistent') is None


def test_manifest_column_dataclass():
    col = ManifestColumn(name='id', description='PK', data_type='integer')
    assert col.name == 'id'
