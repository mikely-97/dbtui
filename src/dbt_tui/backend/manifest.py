"""Parse dbt manifest.json for compiled metadata."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ManifestColumn:
    name: str
    description: str = ''
    data_type: str = ''

@dataclass
class ManifestNode:
    unique_id: str
    name: str
    resource_type: str  # model, test, seed, snapshot, source
    description: str = ''
    columns: list[ManifestColumn] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    materialized: str = ''
    compiled_code: str = ''


def parse_manifest(project_root: Path) -> dict[str, ManifestNode]:
    """Parse target/manifest.json and return nodes keyed by model name."""
    manifest_path = project_root / 'target' / 'manifest.json'
    if not manifest_path.exists():
        return {}

    try:
        data = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    nodes: dict[str, ManifestNode] = {}
    for unique_id, node_data in data.get('nodes', {}).items():
        name = node_data.get('name', '')
        columns = [
            ManifestColumn(
                name=col.get('name', ''),
                description=col.get('description', ''),
                data_type=col.get('data_type', ''),
            )
            for col in node_data.get('columns', {}).values()
        ]
        depends_on_nodes = node_data.get('depends_on', {}).get('nodes', [])
        config = node_data.get('config', {})

        nodes[name] = ManifestNode(
            unique_id=unique_id,
            name=name,
            resource_type=node_data.get('resource_type', ''),
            description=node_data.get('description', ''),
            columns=columns,
            depends_on=depends_on_nodes,
            tags=config.get('tags', []),
            materialized=config.get('materialized', ''),
            compiled_code=node_data.get('compiled_code', ''),
        )

    return nodes


def get_manifest_node(project_root: Path, model_name: str) -> ManifestNode | None:
    """Get manifest metadata for a specific model."""
    nodes = parse_manifest(project_root)
    return nodes.get(model_name)
