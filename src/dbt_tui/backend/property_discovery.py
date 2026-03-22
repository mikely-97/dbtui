"""
Property discovery module for collecting PropertyClaims from dbt configuration sources.

This module provides functions to discover and collect property claims from:
- dbt_project.yml (project-level configurations)
- schema.yml files (model-specific properties and configs)
- model SQL files (inline config() calls)

Performance note: Use PropertyDiscoveryCache when collecting claims for multiple models
to avoid re-reading and re-parsing YAML files.
"""

import re
from typing import TYPE_CHECKING

from ..common.logging import get_logger
from .discovery import (
    PropertyDiscoveryCache,
    collect_project_configs,
    collect_schema_properties,
    find_schema_files,
    get_model_path_parts,
)
from .property_claim import PropertyClaim

logger = get_logger('backend.property_discovery')

if TYPE_CHECKING:
    from .model import DbtModel

__all__ = [
    'PropertyDiscoveryCache',
    'collect_project_configs',
    'collect_schema_properties',
    'collect_model_claims',
    'collect_sql_configs',
    'resolve_property_precedence',
    'get_effective_properties',
    'get_model_path_parts',
    'find_schema_files',
]


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


