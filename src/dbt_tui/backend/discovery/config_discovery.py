"""Config discovery from dbt_project.yml files."""

from pathlib import Path
from typing import TYPE_CHECKING
import yaml

from ..property_claim import PropertyClaim
from ...common.logging import get_logger
from .utils import get_model_path_parts

logger = get_logger('backend.discovery.config_discovery')

if TYPE_CHECKING:
    from ..model import DbtModel
    from . import PropertyDiscoveryCache


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
    cache: 'PropertyDiscoveryCache | None' = None,
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


