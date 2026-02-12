"""
Property writing module for updating YAML configuration files and model SQL.

Supports writing to:
- schema.yml files (properties and configs)
- Model SQL files (config() calls)

Note: PyYAML's yaml.dump() does not preserve comments or formatting.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
import re
import yaml

from ..common.logging import get_logger

if TYPE_CHECKING:
    from .model import DbtModel


logger = get_logger('backend.property_writer')


@dataclass
class WriteResult:
    """Result of a property write operation."""
    success: bool
    message: str
    file_path: Path | None = None


class SchemaYmlWriter:
    """
    Handles reading, modifying, and writing schema.yml files.

    Preserves structure as much as possible by:
    1. Reading the full file
    2. Making targeted modifications to the parsed structure
    3. Writing back with yaml.dump()

    Note: Comments and custom formatting will be lost.
    """

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self._data: dict | None = None

    def load(self) -> dict:
        """Load and parse the schema file."""
        if self._data is None:
            if self.schema_path.exists():
                self._data = yaml.safe_load(self.schema_path.read_text()) or {}
            else:
                self._data = {"version": 2, "models": []}
        return self._data

    def save(self) -> None:
        """Write the modified data back to the file."""
        if self._data is None:
            raise RuntimeError("No data loaded")

        # Ensure parent directory exists
        self.schema_path.parent.mkdir(parents=True, exist_ok=True)

        self.schema_path.write_text(
            yaml.dump(
                self._data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
        )

    def get_or_create_model_entry(self, model_name: str) -> dict:
        """Get existing model entry or create a new one."""
        data = self.load()
        if "models" not in data:
            data["models"] = []

        for model_def in data["models"]:
            if isinstance(model_def, dict) and model_def.get("name") == model_name:
                return model_def

        # Create new entry
        new_entry = {"name": model_name}
        data["models"].append(new_entry)
        return new_entry

    def set_property(
        self,
        model_name: str,
        prop_name: str,
        value: Any,
        kind: Literal["config", "property"]
    ) -> None:
        """Set a property value for a model."""
        model_entry = self.get_or_create_model_entry(model_name)

        if kind == "config":
            if "config" not in model_entry:
                model_entry["config"] = {}
            model_entry["config"][prop_name] = value
        else:
            model_entry[prop_name] = value

    def remove_property(
        self,
        model_name: str,
        prop_name: str,
        kind: Literal["config", "property"]
    ) -> bool:
        """Remove a property. Returns True if property existed."""
        model_entry = self.get_or_create_model_entry(model_name)

        if kind == "config":
            if "config" in model_entry and prop_name in model_entry["config"]:
                del model_entry["config"][prop_name]
                # Clean up empty config block
                if not model_entry["config"]:
                    del model_entry["config"]
                return True
        else:
            if prop_name in model_entry and prop_name != "name":
                del model_entry[prop_name]
                return True
        return False


class SqlConfigWriter:
    """
    Handles modifying config() calls in SQL model files.

    Strategies:
    1. If config() exists: modify the specific kwarg
    2. If config() doesn't exist: add it at the top of the file
    """

    CONFIG_PATTERN = re.compile(
        r"\{\{\s*config\s*\((.*?)\)\s*\}\}",
        re.DOTALL
    )

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._text: str | None = None

    def load(self) -> str:
        """Load the SQL file content."""
        if self._text is None:
            self._text = self.model_path.read_text()
        return self._text

    def save(self) -> None:
        """Write modified content back to file."""
        if self._text is None:
            raise RuntimeError("No content loaded")
        self.model_path.write_text(self._text)

    def has_config(self) -> bool:
        """Check if file has a config() call."""
        return bool(self.CONFIG_PATTERN.search(self.load()))

    def set_config_value(self, key: str, value: Any) -> None:
        """
        Set a config value.

        If config() exists, modifies it. Otherwise, adds new config().
        """
        text = self.load()

        match = self.CONFIG_PATTERN.search(text)
        if match:
            self._modify_existing_config(key, value, match)
        else:
            self._add_new_config(key, value)

    def _modify_existing_config(self, key: str, value: Any, match: re.Match) -> None:
        """Modify an existing config() call."""
        config_content = match.group(1)
        formatted_value = self._format_value(value)

        # Check if key already exists (with = sign)
        key_pattern = re.compile(rf'\b{re.escape(key)}\s*=\s*[^,\)]+')
        if key_pattern.search(config_content):
            # Replace existing value
            new_content = key_pattern.sub(f'{key}={formatted_value}', config_content)
        else:
            # Add new key
            stripped = config_content.strip()
            if stripped:
                # Add to end of existing args
                new_content = f"{config_content.rstrip()}, {key}={formatted_value}"
            else:
                new_content = f"{key}={formatted_value}"

        new_config = f"{{{{ config({new_content}) }}}}"
        self._text = self._text[:match.start()] + new_config + self._text[match.end():]

    def _add_new_config(self, key: str, value: Any) -> None:
        """Add a new config() call at the top of the file."""
        formatted_value = self._format_value(value)
        config_line = f"{{{{ config({key}={formatted_value}) }}}}\n"
        self._text = config_line + self.load()

    def _format_value(self, value: Any) -> str:
        """Format a Python value for Jinja2 config()."""
        if isinstance(value, str):
            # Use single quotes for Jinja2 convention
            escaped = value.replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (list, dict)):
            # For complex types, use Python literal syntax
            return repr(value)
        else:
            return str(value)


def find_or_create_schema_path(model: 'DbtModel') -> Path:
    """
    Find existing schema.yml for a model, or determine where to create one.

    Strategy:
    1. Look for existing schema.yml in model's directory
    2. Look for schema.yml in parent directories (up to project root)
    3. If none exists, return path for new schema.yml in model's directory
    """
    model_dir = model.file_path_full.parent
    project_root = model.project.root_folder

    # Check model directory and parents
    current = model_dir
    while current >= project_root:
        for name in ("schema.yml", "_schema.yml", "models.yml", "_models.yml"):
            candidate = current / name
            if candidate.exists():
                return candidate
        if current == project_root:
            break
        current = current.parent

    # Return default path in model's directory
    return model_dir / "schema.yml"


def write_property_to_schema(
    model: 'DbtModel',
    prop_name: str,
    value: Any,
    kind: Literal["config", "property"],
    schema_path: Path | None = None,
) -> WriteResult:
    """
    Write a property to schema.yml for a model.

    Args:
        model: The DbtModel to write property for
        prop_name: Property name
        value: Property value
        kind: "config" or "property"
        schema_path: Optional specific path; auto-detected if None

    Returns:
        WriteResult indicating success/failure
    """
    try:
        if schema_path is None:
            schema_path = find_or_create_schema_path(model)

        writer = SchemaYmlWriter(schema_path)
        writer.set_property(model.name, prop_name, value, kind)
        writer.save()

        logger.info(f"Wrote {kind} '{prop_name}' to {schema_path.name} for model '{model.name}'")
        return WriteResult(
            success=True,
            message=f"Property '{prop_name}' saved to {schema_path.name}",
            file_path=schema_path
        )
    except Exception as e:
        logger.error(f"Failed to write property '{prop_name}': {e}")
        return WriteResult(
            success=False,
            message=f"Failed to write property: {e}"
        )


def write_property_to_model_sql(
    model: 'DbtModel',
    prop_name: str,
    value: Any,
) -> WriteResult:
    """
    Write a config property to the model's SQL file.

    Note: This only supports config-type properties.
    """
    try:
        writer = SqlConfigWriter(model.file_path_full)
        writer.set_config_value(prop_name, value)
        writer.save()

        logger.info(f"Wrote config '{prop_name}' to {model.file_path_full.name}")
        return WriteResult(
            success=True,
            message=f"Config '{prop_name}' saved to {model.file_path_full.name}",
            file_path=model.file_path_full
        )
    except Exception as e:
        logger.error(f"Failed to write config '{prop_name}': {e}")
        return WriteResult(
            success=False,
            message=f"Failed to write config: {e}"
        )
