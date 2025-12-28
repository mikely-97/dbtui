from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


def get_model_path_parts(
    model_path: Path,
    project_path: Path,
) -> list[str]:
    """
    models/foo/bar/my_model.sql -> ["foo", "bar", "my_model"]
    """
    models_dir = project_path / "models"
    rel = model_path.resolve().relative_to(models_dir.resolve())
    return list(rel.with_suffix("").parts)


def find_schema_files(
    model_path: Path,
    project_path: Path,
) -> list[Path]:
    schema_files: list[Path] = []

    model_dir_path_abs = model_path.parent.resolve()
    project_dir_path_abs = project_path.resolve()
    
    yml_targets = [i for i in model_dir_path_abs.relative_to(project_dir_path_abs).parents if not i == Path('.')]

    for target in yml_targets:
        for ext in ("*.yml", "*.yaml"):
            schema_files.extend(target.glob(ext))


    return schema_files



@dataclass
class PropertyClaim:
    source_type: Literal["dbt_project.yml", "schema.yml", "model.sql"]
    source_path: Path
    name: str
    value: Any
    kind: Literal["config", "property"]

import yaml
import re

def collect_project_configs(
    model_path: Path,
    project_path: Path,
) -> list[PropertyClaim]:
    claims: list[PropertyClaim] = []

    project_file = project_path / "dbt_project.yml"
    if not project_file.exists():
        return claims

    data = yaml.safe_load(project_file.read_text()) or {}
    models = data.get("models", {})

    model_parts = get_model_path_parts(model_path, project_path)

    def walk(node, path_index: int):
        """
        node: current yaml dict
        path_index: where we are in model_parts
        """
        if not isinstance(node, dict):
            return

        # collect configs at this level
        for k, v in node.items():
            if isinstance(k, str) and k.startswith("+"):
                claims.append(
                    PropertyClaim(
                        source_type="dbt_project.yml",
                        source_path=project_file,
                        name=k[1:],
                        value=v,
                        kind="config",
                    )
                )

        # descend if possible
        if path_index >= len(model_parts):
            return

        next_key = model_parts[path_index]
        if next_key in node:
            walk(node[next_key], path_index + 1)

    # dbt_project.yml always has: models: <package_name>: ...
    for package_node in models.values():
        walk(package_node, 0)

    return claims




def collect_schema_properties(
    schema_file: Path,
    model_name: str,
) -> list[PropertyClaim]:
    claims: list[PropertyClaim] = []

    try:
        data = yaml.safe_load(schema_file.read_text()) or {}
    except Exception:
        return claims  # invalid yaml, dbt would scream; you quietly ignore

    models = data.get("models", [])

    for model in models:
        if model.get("name") != model_name:
            continue

        for key, value in model.items():
            if key == "config":
                for ck, cv in (value or {}).items():
                    claims.append(
                        PropertyClaim(
                            source_type="schema.yml",
                            source_path=schema_file,
                            name=ck,
                            value=cv,
                            kind="config",
                        )
                    )
            elif key != "name":
                claims.append(
                    PropertyClaim(
                        source_type="schema.yml",
                        source_path=schema_file,
                        name=key,
                        value=value,
                        kind="property",
                    )
                )

    return claims


CONFIG_CALL_RE = re.compile(
    r"config\s*\((.*?)\)",
    re.DOTALL,
)


def collect_sql_configs(model_path: Path) -> list[PropertyClaim]:
    claims: list[PropertyClaim] = []

    text = model_path.read_text()
    matches = CONFIG_CALL_RE.findall(text)

    for match in matches:
        # extremely naive kwarg parsing
        parts = re.split(r",(?![^\[\]\(\)]*[\]\)])", match)

        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            claims.append(
                PropertyClaim(
                    source_type="model.sql",
                    source_path=model_path,
                    name=key.strip(),
                    value=value.strip(),
                    kind="config",
                )
            )

    return claims

def collect_model_claims(
    model_path: Path,
    project_path: Path,
) -> list[PropertyClaim]:
    claims: list[PropertyClaim] = []
    model_name = model_path.stem

    # dbt_project.yml
    claims.extend(collect_project_configs(model_path, project_path))

    # schema.yml files discovered automatically
    schema_files = find_schema_files(model_path, project_path)
    for schema_file in schema_files:
        claims.extend(
            collect_schema_properties(schema_file, model_name)
        )

    # model.sql
    claims.extend(collect_sql_configs(model_path))

    return claims


print(
    collect_model_claims(
        Path('models/mart/users_daily_stat.sql'),
        Path('.'),
    )
)

