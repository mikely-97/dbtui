"""Schema discovery from schema.yml files."""

from pathlib import Path
from typing import TYPE_CHECKING
import yaml

from ..property_claim import PropertyClaim
from ...common.logging import get_logger
from .utils import find_schema_files

logger = get_logger('backend.discovery.schema_discovery')

if TYPE_CHECKING:
    from ..model import DbtModel
    from . import PropertyDiscoveryCache


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


def collect_schema_properties(
    model: 'DbtModel',
    schema_file: Path | None = None,
    cache: 'PropertyDiscoveryCache | None' = None,
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


