"""Impact analysis — find all downstream dependents of a model."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project import DbtProject
    from dbt_tui.common.entity import DbtEntityAbstract


@dataclass
class ImpactResult:
    total_affected: int
    by_depth: dict[int, list['DbtEntityAbstract']]
    all_affected: list['DbtEntityAbstract']


def analyze_impact(project: 'DbtProject', model: 'DbtEntityAbstract', max_depth: int = 10) -> ImpactResult:
    """Find all downstream entities affected if this model changes."""
    graph = project.graph
    by_depth: dict[int, list['DbtEntityAbstract']] = {}
    visited: set = {model}
    frontier = [model]

    for depth in range(1, max_depth + 1):
        next_frontier = []
        for node in frontier:
            for child in graph.successors(node):
                if child not in visited:
                    visited.add(child)
                    next_frontier.append(child)
        if not next_frontier:
            break
        by_depth[depth] = sorted(next_frontier, key=lambda n: n.name)
        frontier = next_frontier

    all_affected = []
    for depth in sorted(by_depth.keys()):
        all_affected.extend(by_depth[depth])

    return ImpactResult(
        total_affected=len(all_affected),
        by_depth=by_depth,
        all_affected=all_affected,
    )
