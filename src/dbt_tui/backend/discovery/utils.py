"""Utility functions for property discovery."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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
        if hasattr(model_path, 'project'):
            project = model_path.project
    except Exception:
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
