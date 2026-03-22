"""Property discovery package for collecting PropertyClaims from dbt configuration sources."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from ...common.logging import get_logger
from ..property_claim import PropertyClaim
from .config_discovery import collect_project_configs
from .schema_discovery import collect_schema_properties
from .utils import find_schema_files, get_model_path_parts

logger = get_logger('backend.discovery')

if TYPE_CHECKING:
    from ..model import DbtModel
    from ..project import DbtProject

__all__ = [
    'PropertyDiscoveryCache',
    'PropertyClaim',
    'collect_project_configs',
    'collect_schema_properties',
    'get_model_path_parts',
    'find_schema_files',
]


@dataclass
class PropertyDiscoveryCache:
    """
    Cache for parsed YAML files to avoid re-reading during property collection.

    This dramatically improves performance when collecting properties for many models,
    as each file is only read and parsed once.
    """
    project_path: Path = None
    dbt_project_data: dict = field(default_factory=dict)
    schema_files_by_dir: dict = field(default_factory=dict)
    schema_data_by_path: dict = field(default_factory=dict)
    models_by_name_in_schemas: dict = field(default_factory=dict)
    _initialized: bool = False

    def initialize(self, project: 'DbtProject') -> None:
        """
        Initialize the cache by reading all relevant files once.

        Args:
            project: The DbtProject to cache data for
        """
        if self._initialized:
            return

        self.project_path = project.root_folder

        # 1. Parse dbt_project.yml once
        project_file = self.project_path / "dbt_project.yml"
        if project_file.exists():
            try:
                self.dbt_project_data = yaml.safe_load(project_file.read_text()) or {}
            except Exception as e:
                logger.warning(f"Failed to parse {project_file}: {e}")
                self.dbt_project_data = {}

        # 2. Find and parse all schema files in the project
        self._discover_schema_files(project)

        # 3. Build index of models in schema files
        self._index_models_in_schemas()

        self._initialized = True

    def _discover_schema_files(self, project: 'DbtProject') -> None:
        """Find all schema.yml files in the project and parse them."""
        seen_paths: set[Path] = set()

        for models_path in project.full_models_paths:
            if not models_path.exists():
                continue
            for root, _, _files in models_path.walk():
                root_path = Path(root)
                for ext in ("yml", "yaml"):
                    for schema_file in root_path.glob(f"*.{ext}"):
                        stem = schema_file.stem.lower()
                        if stem in ("schema", "models", "_schema", "_models"):
                            abs_path = schema_file.resolve()
                            if abs_path in seen_paths:
                                continue
                            seen_paths.add(abs_path)

                            # Track by directory for path-based lookup
                            if root_path not in self.schema_files_by_dir:
                                self.schema_files_by_dir[root_path] = []
                            self.schema_files_by_dir[root_path].append(schema_file)

                            # Parse and cache the content
                            try:
                                data = yaml.safe_load(schema_file.read_text()) or {}
                                self.schema_data_by_path[schema_file] = data
                            except Exception as e:
                                logger.debug(f"Failed to parse {schema_file}: {e}")
                                self.schema_data_by_path[schema_file] = {}

    def _index_models_in_schemas(self) -> None:
        """Build an index of model names to their schema file definitions."""
        for schema_path, data in self.schema_data_by_path.items():
            models_list = data.get("models", [])
            if not isinstance(models_list, list):
                continue
            for model_def in models_list:
                if not isinstance(model_def, dict):
                    continue
                model_name = model_def.get("name")
                if model_name:
                    if model_name not in self.models_by_name_in_schemas:
                        self.models_by_name_in_schemas[model_name] = []
                    self.models_by_name_in_schemas[model_name].append((schema_path, model_def))

    def get_schema_files_for_model(self, model: 'DbtModel') -> list[Path]:
        """Get schema files relevant to a model (in its directory and ancestors)."""
        result: list[Path] = []
        model_dir = model.file_path_full.parent.resolve()
        project_dir = self.project_path.resolve()

        current = model_dir
        while current >= project_dir:
            if current in self.schema_files_by_dir:
                result.extend(self.schema_files_by_dir[current])
            if current == project_dir:
                break
            current = current.parent

        return result

    def get_model_definitions(self, model_name: str) -> list[tuple[Path, dict]]:
        """Get all schema definitions for a model by name."""
        return self.models_by_name_in_schemas.get(model_name, [])
