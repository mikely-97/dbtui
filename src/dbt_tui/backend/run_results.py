"""Parse dbt run_results.json for last run status."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project import DbtProject


@dataclass
class ModelRunResult:
    unique_id: str
    status: str          # pass, fail, error, warn, skipped
    execution_time: float
    message: str
    adapter_response: str


def parse_run_results(project_root: Path) -> dict[str, ModelRunResult]:
    """Parse target/run_results.json and return results keyed by model name."""
    results_path = project_root / 'target' / 'run_results.json'
    if not results_path.exists():
        return {}

    try:
        data = json.loads(results_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    results: dict[str, ModelRunResult] = {}
    for result in data.get('results', []):
        unique_id = result.get('unique_id', '')
        # unique_id format: model.project_name.model_name
        parts = unique_id.split('.')
        model_name = parts[-1] if parts else unique_id

        results[model_name] = ModelRunResult(
            unique_id=unique_id,
            status=result.get('status', 'unknown'),
            execution_time=result.get('execution_time', 0.0),
            message=result.get('message', ''),
            adapter_response=str(result.get('adapter_response', '')),
        )

    return results


def get_model_run_result(project_root: Path, model_name: str) -> ModelRunResult | None:
    """Get run result for a specific model."""
    results = parse_run_results(project_root)
    return results.get(model_name)
