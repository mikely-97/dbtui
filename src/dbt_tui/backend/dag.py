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


def get_dag_node_list(project: 'DbtProject', focal: 'DbtEntityAbstract', depth: int = 2) -> list['DbtEntityAbstract']:
    """Return nodes visible in DAG ordered: ancestors (deep→shallow), focal, descendants (shallow→deep)."""
    graph = project.graph
    ancestors = _walk_by_depth(graph, focal, depth, graph.predecessors)
    descendants = _walk_by_depth(graph, focal, depth, graph.successors)

    result: list['DbtEntityAbstract'] = []
    for d in sorted(ancestors.keys()):        # -depth … -1
        result.extend(ancestors[d])
    result.append(focal)
    for d in sorted(descendants.keys()):      # 1 … depth
        result.extend(descendants[d])
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


def _mermaid_id(entity: 'DbtEntityAbstract') -> str:
    """Generate a valid Mermaid node ID from an entity name."""
    return entity.name.replace('.', '_').replace('-', '_')


def render_dag_mermaid(project: 'DbtProject', focal: 'DbtEntityAbstract', depth: int = 2) -> str:
    """Render a Mermaid flowchart centred on focal entity."""
    graph = project.graph
    ancestors = _walk_by_depth(graph, focal, depth, graph.predecessors)
    descendants = _walk_by_depth(graph, focal, depth, graph.successors)

    lines = ['graph LR']

    # Collect all visible nodes
    all_nodes = []
    for d in sorted(ancestors.keys()):
        all_nodes.extend(ancestors[d])
    all_nodes.append(focal)
    for d in sorted(descendants.keys()):
        all_nodes.extend(descendants[d])

    # Node definitions with shapes
    for node in all_nodes:
        node_id = _mermaid_id(node)
        if node is focal:
            lines.append(f'    {node_id}[["**{node.name}**"]]')
        elif node.entity_type == 'source':
            lines.append(f'    {node_id}[("{node.name}")]')
        elif node.entity_type == 'macro':
            lines.append(f'    {node_id}{{{node.name}}}')
        else:
            lines.append(f'    {node_id}[{node.name}]')

    # Edges
    for node in all_nodes:
        node_id = _mermaid_id(node)
        for child in graph.successors(node):
            if child in all_nodes:
                lines.append(f'    {node_id} --> {_mermaid_id(child)}')

    return '\n'.join(lines)
