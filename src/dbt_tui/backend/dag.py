"""ASCII DAG renderer for dbt-tui."""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from dbt_tui.backend.project import DbtProject
    from dbt_tui.common.entity import DbtEntityAbstract


def _walk_by_depth(graph, focal, depth, get_neighbors: Callable):
    """Walk graph by depth using provided neighbor function (predecessors or successors)."""
    result = {}
    visited = {focal}
    frontier = [focal]
    for d in range(1, depth + 1):
        next_frontier = []
        for node in frontier:
            for neighbor in get_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.append(neighbor)
        if not next_frontier:
            break
        key = -d if get_neighbors == graph.predecessors else d
        result[key] = sorted(next_frontier, key=lambda n: n.name)
        frontier = next_frontier
    return result


def _format_node(entity, focal, width=20):
    label = entity.name
    if entity.entity_type != "model":
        label = f'[{entity.entity_type[0]}] {label}'
    if entity is focal:
        return f'[ {label} ]'.center(width)
    return label.center(width)


def render_dag_ascii(project: 'DbtProject', focal: 'DbtEntityAbstract', depth: int = 2) -> str:
    """Render an ASCII DAG centred on focal entity."""
    graph = project.graph
    ancestors = _walk_by_depth(graph, focal, depth, graph.predecessors)
    descendants = _walk_by_depth(graph, focal, depth, graph.successors)

    lines = []

    for d in sorted(ancestors.keys()):  # -depth … -1
        nodes = ancestors[d]
        lines.append('  '.join(_format_node(n, focal) for n in nodes))
        lines.append('  '.join('|'.center(20) for _ in nodes))

    lines.append(_format_node(focal, focal, width=max(24, len(focal.name) + 4)))

    for d in sorted(descendants.keys()):  # 1 … depth
        nodes = descendants[d]
        lines.append('  '.join('|'.center(20) for _ in nodes))
        lines.append('  '.join(_format_node(n, focal) for n in nodes))

    return '\n'.join(lines)
