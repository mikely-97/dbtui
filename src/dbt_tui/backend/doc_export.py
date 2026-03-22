"""Export model documentation as markdown."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import DbtModel
    from .project import DbtProject


def export_model_markdown(project: 'DbtProject', model: 'DbtModel') -> str:
    """Generate a markdown documentation page for a model."""
    lines = [f'# {model.name}', '']

    # Description from property claims
    if model.property_claims:
        try:
            desc = model.property_claims.get_value('description')
            if desc:
                lines.extend([str(desc), ''])
        except Exception:
            pass

    # Metadata
    lines.append('## Metadata')
    lines.append(f'- **File:** `{model.file_path_relative}`')
    lines.append(f'- **Materialization:** {model.materialized}')
    if model.tags:
        lines.append(f'- **Tags:** {", ".join(model.tags)}')
    lines.append('')

    # Dependencies
    parents = list(project.graph.predecessors(model))
    children = list(project.graph.successors(model))

    if parents:
        lines.append('## Dependencies (upstream)')
        for p in sorted(parents, key=lambda n: n.name):
            lines.append(f'- `{p.name}` ({p.entity_type})')
        lines.append('')

    if children:
        lines.append('## Dependents (downstream)')
        for c in sorted(children, key=lambda n: n.name):
            lines.append(f'- `{c.name}` ({c.entity_type})')
        lines.append('')

    # Column lineage
    try:
        from .lineage import extract_columns
        columns = extract_columns(model)
        if columns:
            lines.append('## Columns')
            lines.append('| Column | Source Model | Source Column |')
            lines.append('|--------|-------------|--------------|')
            for col in columns:
                src_model = col.source_model or '-'
                src_col = col.source_column or col.source_expression or '-'
                lines.append(f'| `{col.name}` | {src_model} | {src_col} |')
            lines.append('')
    except Exception:
        pass

    # SQL
    lines.append('## SQL')
    lines.append('```sql')
    lines.append(model.text)
    lines.append('```')

    return '\n'.join(lines)
