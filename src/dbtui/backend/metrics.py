"""
Performance metrics for dbtui.

Provides timing instrumentation for project loading and other operations.
Metrics can be accessed after project load to diagnose performance issues.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec('P')
T = TypeVar('T')


@dataclass
class LoadMetrics:
    """Metrics collected during project loading."""
    model_count: int = 0
    parse_dbt_project_yml_ms: float = 0.0
    load_models_ms: float = 0.0
    populate_graph_ms: float = 0.0
    collect_property_claims_ms: float = 0.0
    total_load_ms: float = 0.0

    def __str__(self) -> str:
        return (
            f"Load metrics ({self.model_count} models):\n"
            f"  parse_dbt_project.yml: {self.parse_dbt_project_yml_ms:.1f}ms\n"
            f"  load_models: {self.load_models_ms:.1f}ms\n"
            f"  populate_graph: {self.populate_graph_ms:.1f}ms\n"
            f"  collect_property_claims: {self.collect_property_claims_ms:.1f}ms\n"
            f"  total: {self.total_load_ms:.1f}ms"
        )

    def as_dict(self) -> dict:
        """Return metrics as a dictionary for serialization."""
        return {
            'model_count': self.model_count,
            'parse_dbt_project_yml_ms': self.parse_dbt_project_yml_ms,
            'load_models_ms': self.load_models_ms,
            'populate_graph_ms': self.populate_graph_ms,
            'collect_property_claims_ms': self.collect_property_claims_ms,
            'total_load_ms': self.total_load_ms,
        }


class Timer:
    """Context manager for timing code blocks."""

    def __init__(self):
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> 'Timer':
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000


def timed(func: Callable[P, T]) -> Callable[P, tuple[T, float]]:
    """
    Decorator that returns both result and elapsed time in ms.

    Usage:
        result, elapsed_ms = timed(my_function)(arg1, arg2)
    """
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> tuple[T, float]:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return result, elapsed_ms
    return wrapper
