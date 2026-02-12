"""
Property discovery module for collecting PropertyClaims from dbt configuration sources.

This module provides functions to discover and collect property claims from:
- dbt_project.yml (project-level configurations)
- schema.yml files (model-specific properties and configs)
- model SQL files (inline config() calls)

Performance note: Use PropertyDiscoveryCache when collecting claims for multiple models
to avoid re-reading and re-parsing YAML files.
"""

from pathlib import Path
from typing import TYPE_CHECKING
import yaml
import re
from dataclasses import dataclass, field

from .property_claim import PropertyClaim
from ..common.logging import get_logger

logger = get_logger('backend.property_discovery')

if TYPE_CHECKING:
    from .model import DbtModel
    from .project import DbtProject


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
            for root, _, files in models_path.walk():
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


def get_model_path_parts(
    model_path: Path,
    project_path: Path,
) -> list[str]:
    """
    Extract hierarchical path components for a model relative to model-paths.

    Args:
        model_path: Absolute path to the model SQL file
        project_path: Absolute path to the dbt project root

    Returns:
        List of path components from model root to model name (without .sql)

    Example:
        models/foo/bar/my_model.sql -> ["foo", "bar", "my_model"]
    """
    # Try to find the model within configured model-paths
    project = None
    try:
        # If we have a DbtModel instance, use its project's model paths
        from .project import DbtProject
        if hasattr(model_path, 'project'):
            project = model_path.project
    except:
        pass

    # Try configured model paths if available
    if project and hasattr(project, 'full_models_paths'):
        for models_root in project.full_models_paths:
            try:
                rel = model_path.resolve().relative_to(models_root.resolve())
                return list(rel.with_suffix("").parts)
            except ValueError:
                continue

    # Fallback: look for "models" directory
    try:
        models_dir = project_path / "models"
        if models_dir.exists():
            rel = model_path.resolve().relative_to(models_dir.resolve())
            return list(rel.with_suffix("").parts)
    except ValueError:
        pass

    # Last resort: relative to project root
    rel = model_path.resolve().relative_to(project_path.resolve())
    parts = list(rel.with_suffix("").parts)

    # Remove common prefixes like "models", "vanilla", "complex_config" if they exist
    # This is project-specific and might need adjustment
    return parts


def find_schema_files(
    model_path: Path,
    project_path: Path,
) -> list[Path]:
    """
    Find all schema YAML files that could contain properties for the given model.

    Searches from the model's directory up to the project root for files named:
    - schema.yml, schema.yaml
    - models.yml, models.yaml
    - _schema.yml, _schema.yaml
    - _models.yml, _models.yaml

    Args:
        model_path: Absolute path to the model SQL file
        project_path: Absolute path to the dbt project root

    Returns:
        List of paths to schema YAML files
    """
    schema_files: list[Path] = []

    model_dir_path_abs = model_path.parent.resolve()
    project_dir_path_abs = project_path.resolve()

    # Walk up from model directory to project root
    current = model_dir_path_abs
    while current >= project_dir_path_abs:
        for ext in ("yml", "yaml"):
            for schema_file in current.glob(f"*.{ext}"):
                # Check if it's a schema file by name
                stem = schema_file.stem.lower()
                if stem in ("schema", "models", "_schema", "_models"):
                    schema_files.append(schema_file)

        if current == project_dir_path_abs:
            break
        current = current.parent

    return schema_files


def _extract_schema_claims(
    schema_path: Path,
    model_def: dict,
    model: 'DbtModel',
) -> list[PropertyClaim]:
    """
    Extract property claims from a model definition dict.

    This is the shared implementation used by both cached and non-cached paths.

    Args:
        schema_path: Path to the schema file (for source tracking)
        model_def: The model definition dict from YAML
        model: The DbtModel instance

    Returns:
        List of PropertyClaim objects extracted from the model definition
    """
    claims: list[PropertyClaim] = []

    for key, value in model_def.items():
        if key == "name":
            continue
        elif key == "config":
            # Config block contains config-type properties
            if isinstance(value, dict):
                for ck, cv in value.items():
                    claims.append(
                        PropertyClaim(
                            source_type="schema.yml",
                            source_path=schema_path,
                            model=model,
                            name=ck,
                            value=cv,
                            kind="config",
                        )
                    )
        else:
            # Other keys are regular properties (description, columns, tests, etc.)
            claims.append(
                PropertyClaim(
                    source_type="schema.yml",
                    source_path=schema_path,
                    model=model,
                    name=key,
                    value=value,
                    kind="property",
                )
            )

    return claims


def _walk_project_configs(
    node: dict,
    model: 'DbtModel',
    model_parts: list[str],
    project_file: Path,
    path_index: int,
    yaml_path: str,
    parts_matched: list[str],
    claims: list[PropertyClaim],
) -> None:
    """
    Recursively walk the dbt_project.yml hierarchy to collect configs.

    This is the shared implementation used by both cached and non-cached paths.

    Args:
        node: Current YAML dict being examined
        model: The DbtModel instance
        model_parts: List of model path components
        project_file: Path to dbt_project.yml
        path_index: Current index in model_parts
        yaml_path: Dot-separated path for tracking precedence
        parts_matched: List of model path parts that have been matched
        claims: List to append claims to (modified in place)
    """
    if not isinstance(node, dict):
        return

    # Collect configs at this level (keys starting with +)
    for k, v in node.items():
        if isinstance(k, str) and k.startswith("+"):
            prop_name = k[1:]
            # Check if this config is effective for this model
            effective = parts_matched == model_parts[:len(parts_matched)]

            claims.append(
                PropertyClaim(
                    source_type="dbt_project.yml",
                    source_path=project_file,
                    model=model,
                    name=prop_name,
                    value=v,
                    yaml_path=yaml_path,
                    effective=effective,
                    kind="config",
                )
            )

    # Try to descend further if we have more path parts to match
    if path_index < len(model_parts):
        next_key = model_parts[path_index]
        if next_key in node:
            _walk_project_configs(
                node[next_key],
                model,
                model_parts,
                project_file,
                path_index + 1,
                f"{yaml_path}.{next_key}",
                parts_matched + [next_key],
                claims,
            )


def collect_project_configs(
    model: 'DbtModel',
    cache: PropertyDiscoveryCache | None = None,
) -> list[PropertyClaim]:
    """
    Collect property claims from dbt_project.yml for a specific model.

    Walks the YAML hierarchy matching the model's path structure to find
    applicable configurations. Configurations can use the + prefix to indicate
    they apply to models.

    Args:
        model: The DbtModel instance to collect configs for
        cache: Optional cache with pre-parsed dbt_project.yml data

    Returns:
        List of PropertyClaim objects from dbt_project.yml
    """
    claims: list[PropertyClaim] = []
    project_path = model.project.root_folder
    model_path = model.file_path_full
    project_file = project_path / "dbt_project.yml"

    # Get data from cache or read from file
    if cache is not None and cache._initialized:
        data = cache.dbt_project_data
    else:
        if not project_file.exists():
            return claims
        try:
            data = yaml.safe_load(project_file.read_text()) or {}
        except Exception as e:
            logger.warning(f"Failed to parse {project_file}: {e}")
            return claims

    if not data:
        return claims

    models = data.get("models", {})
    if not models:
        return claims

    model_parts = get_model_path_parts(model_path, project_path)
    package_name = data.get("name", "")

    # Start walking from package level
    if package_name in models:
        _walk_project_configs(
            models[package_name],
            model,
            model_parts,
            project_file,
            0,
            f"models.{package_name}",
            [],
            claims,
        )

    # Also check for wildcard configs at root models level
    for k, v in models.items():
        if isinstance(k, str) and k.startswith("+"):
            prop_name = k[1:]
            claims.append(
                PropertyClaim(
                    source_type="dbt_project.yml",
                    source_path=project_file,
                    model=model,
                    name=prop_name,
                    value=v,
                    yaml_path="models",
                    effective=True,  # Root level applies to all
                    kind="config",
                )
            )

    return claims


def collect_schema_properties(
    model: 'DbtModel',
    schema_file: Path | None = None,
    cache: PropertyDiscoveryCache | None = None,
) -> list[PropertyClaim]:
    """
    Collect property claims from schema.yml files for a specific model.

    Looks for the model by name in schema files and extracts all properties
    and configs.

    Args:
        model: The DbtModel instance to collect properties for
        schema_file: Optional specific schema file to read (for backward compat)
        cache: Optional cache with pre-parsed schema data

    Returns:
        List of PropertyClaim objects from schema files
    """
    claims: list[PropertyClaim] = []

    # Use cached path if cache is available and initialized
    if cache is not None and cache._initialized:
        model_defs = cache.get_model_definitions(model.name)
        for schema_path, model_def in model_defs:
            claims.extend(_extract_schema_claims(schema_path, model_def, model))
        return claims

    # Non-cached path: read from specific file or find schema files
    if schema_file is not None:
        schema_files = [schema_file]
    else:
        schema_files = find_schema_files(model.file_path_full, model.project.root_folder)

    for sf in schema_files:
        try:
            data = yaml.safe_load(sf.read_text()) or {}
        except Exception as e:
            logger.debug(f"Failed to parse {sf}: {e}")
            continue

        models_list = data.get("models", [])
        if not isinstance(models_list, list):
            continue

        for model_def in models_list:
            if not isinstance(model_def, dict):
                continue
            if model_def.get("name") != model.name:
                continue
            claims.extend(_extract_schema_claims(sf, model_def, model))

    return claims


def collect_sql_configs(
    model: 'DbtModel',
) -> list[PropertyClaim]:
    """
    Collect property claims from config() calls in the model's SQL file.

    Uses the model's already-parsed Jinja2 template to extract config
    arguments. Falls back to regex-based parsing if template parsing fails.

    Args:
        model: The DbtModel instance to collect configs from

    Returns:
        List of PropertyClaim objects from config() calls
    """
    claims: list[PropertyClaim] = []
    model_path = model.file_path_full

    try:
        # Use the already parsed template from the model
        parsed = model.parsed_template

        # Find all config() calls
        from jinja2.nodes import Call
        config_calls = [node for node in parsed.find_all(Call) if node.node.name == 'config']

        for call in config_calls:
            # Extract kwargs from the config call
            for kwarg in call.kwargs:
                # Extract the value, handling different node types
                if hasattr(kwarg.value, 'value'):
                    value = kwarg.value.value
                else:
                    value = str(kwarg.value)

                claims.append(
                    PropertyClaim(
                        source_type="model",
                        source_path=model_path,
                        model=model,
                        name=kwarg.key,
                        value=value,
                        kind="config",
                    )
                )
    except Exception as e:
        logger.debug(f"Jinja2 parsing failed for {model_path}, falling back to regex: {e}")

        # Fallback to regex-based parsing
        try:
            text = model_path.read_text()
            config_call_re = re.compile(r"\{\{\s*config\s*\((.*?)\)\s*\}\}", re.DOTALL)
            matches = config_call_re.findall(text)

            for match in matches:
                # Naive kwarg parsing - splits on commas not inside brackets/parens
                parts = re.split(r",(?![^\[\]\(\)]*[\]\)])", match)

                for part in parts:
                    if "=" not in part:
                        continue
                    key, value = part.split("=", 1)
                    # Clean up the value
                    cleaned_value = value.strip().strip('"').strip("'")

                    claims.append(
                        PropertyClaim(
                            source_type="model",
                            source_path=model_path,
                            model=model,
                            name=key.strip(),
                            value=cleaned_value,
                            kind="config",
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to parse SQL configs from {model_path}: {e}")

    return claims


def collect_model_claims(
    model: 'DbtModel',
    cache: PropertyDiscoveryCache | None = None,
) -> list[PropertyClaim]:
    """
    Collect all property claims for a model from all sources.

    This is the main entry point for property discovery. It collects claims from:
    1. dbt_project.yml (project-level configs)
    2. schema.yml files (model properties and configs)
    3. Model SQL file (inline config() calls)

    Args:
        model: The DbtModel instance to collect all properties for
        cache: Optional PropertyDiscoveryCache for better performance

    Returns:
        List of all PropertyClaim objects for the model
    """
    claims: list[PropertyClaim] = []

    # 1. Collect from dbt_project.yml
    claims.extend(collect_project_configs(model, cache))

    # 2. Collect from schema.yml files
    claims.extend(collect_schema_properties(model, cache=cache))

    # 3. Collect from model SQL file (no caching needed - already parsed in model)
    claims.extend(collect_sql_configs(model))

    return claims


def resolve_property_precedence(
    claims: list[PropertyClaim],
) -> dict[str, PropertyClaim]:
    """
    Resolve property precedence for a list of claims.

    When multiple claims exist for the same property, dbt's precedence rules are:
    1. Model-level config() in SQL (highest)
    2. schema.yml config or properties
    3. dbt_project.yml (more specific paths win over general ones) (lowest)

    Args:
        claims: List of PropertyClaim objects to resolve

    Returns:
        Dictionary mapping property names to their winning PropertyClaim
    """
    properties: dict[str, PropertyClaim] = {}

    for claim in claims:
        if claim.name not in properties:
            properties[claim.name] = claim
        else:
            # Compare with existing claim using the __gt__ method
            try:
                if claim > properties[claim.name]:
                    properties[claim.name] = claim
            except Exception as e:
                # Log conflicts but keep the existing one
                logger.warning(
                    f"Property conflict for '{claim.name}' in model {claim.model.name}: {e}"
                )

    return properties


def get_effective_properties(
    model: 'DbtModel',
) -> dict[str, any]:
    """
    Get the effective property values for a model after resolving precedence.

    This is a convenience function that collects all claims and resolves
    precedence, returning just the final property values.

    Args:
        model: The DbtModel instance to get effective properties for

    Returns:
        Dictionary mapping property names to their effective values
    """
    claims = collect_model_claims(model)
    resolved = resolve_property_precedence(claims)
    return {name: claim.value for name, claim in resolved.items()}


# ============================================================================
# Cached versions for backward compatibility
# These now simply call the unified functions with cache parameter
# ============================================================================


def collect_project_configs_cached(
    model: 'DbtModel',
    cache: PropertyDiscoveryCache,
) -> list[PropertyClaim]:
    """
    Collect property claims from dbt_project.yml using cached data.

    This is a compatibility wrapper that calls collect_project_configs with cache.

    Args:
        model: The DbtModel instance to collect configs for
        cache: PropertyDiscoveryCache with pre-parsed dbt_project.yml

    Returns:
        List of PropertyClaim objects from dbt_project.yml
    """
    return collect_project_configs(model, cache)


def collect_schema_properties_cached(
    model: 'DbtModel',
    cache: PropertyDiscoveryCache,
) -> list[PropertyClaim]:
    """
    Collect property claims from schema.yml files using cached data.

    This is a compatibility wrapper that calls collect_schema_properties with cache.

    Args:
        model: The DbtModel instance to collect properties for
        cache: PropertyDiscoveryCache with pre-parsed schema files

    Returns:
        List of PropertyClaim objects from schema files
    """
    return collect_schema_properties(model, cache=cache)


def collect_model_claims_cached(
    model: 'DbtModel',
    cache: PropertyDiscoveryCache,
) -> list[PropertyClaim]:
    """
    Collect all property claims for a model using cached YAML data.

    This is a compatibility wrapper that calls collect_model_claims with cache.

    Args:
        model: The DbtModel instance to collect all properties for
        cache: PropertyDiscoveryCache with pre-parsed YAML files

    Returns:
        List of all PropertyClaim objects for the model
    """
    return collect_model_claims(model, cache)
