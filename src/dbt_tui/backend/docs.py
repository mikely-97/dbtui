"""Documentation collection from dbt property claims."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dbt_tui.backend.model import DbtModel


@dataclass
class ColumnDoc:
    name: str
    description: str = ''
    tests: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ModelDocs:
    description: str = ''
    columns: dict[str, ColumnDoc] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = []
        if self.description:
            lines.append(f'{self.description}\n')
        if self.tags:
            lines.append(f'**Tags:** {", ".join(self.tags)}\n')
        if self.tests:
            lines.append(f'**Tests:** {", ".join(self.tests)}\n')
        if self.columns:
            lines.append('\n## Columns\n')
            for col_name, col in self.columns.items():
                entry = f'**{col_name}**'
                if col.description:
                    entry += f': {col.description}'
                if col.tests:
                    entry += f' *(tests: {", ".join(col.tests)})*'
                lines.append(entry + '\n')
        return '\n'.join(lines) if lines else '*No documentation available.*'


def collect_docs(model: DbtModel) -> ModelDocs:
    """Build ModelDocs from the model's property claims."""
    docs = ModelDocs()

    for claim in (model.property_claims or []):
        if claim.source_type != 'schema.yml':
            continue

        if claim.name == 'description' and isinstance(claim.value, str):
            docs.description = claim.value

        elif claim.name == 'tags':
            val = claim.value
            if isinstance(val, list):
                docs.tags = [str(t) for t in val]
            elif isinstance(val, str):
                docs.tags = [val]

        elif claim.name == 'columns' and isinstance(claim.value, list):
            for col_data in claim.value:
                if not isinstance(col_data, dict):
                    continue
                col_name = col_data.get('name', '')
                docs.columns[col_name] = ColumnDoc(
                    name=col_name,
                    description=col_data.get('description', ''),
                    tests=[
                        str(t) if not isinstance(t, dict) else next(iter(t.keys()))
                        for t in col_data.get('tests', [])
                    ],
                    tags=col_data.get('tags', []),
                )

        elif claim.name == 'tests' and isinstance(claim.value, list):
            docs.tests = [
                str(t) if not isinstance(t, dict) else next(iter(t.keys()))
                for t in claim.value
            ]

    return docs
