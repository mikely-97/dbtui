"""Seed entity representing a dbt seed (CSV file)."""
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from dbt_tui.common.entity import DbtEntityAbstract, EntityType

if TYPE_CHECKING:
    from .project import DbtProject


class DbtSeed(DbtEntityAbstract):
    """Represents a dbt seed (CSV data file)."""

    _file_path_full: Path
    project: 'DbtProject'

    def __init__(self, file_path: Path, project: 'DbtProject'):
        self._file_path_full = file_path
        self.project = project

    @property
    def name(self) -> str:
        return self._file_path_full.stem

    @property
    def entity_type(self) -> EntityType:
        return "seed"

    @property
    def text(self) -> str:
        """Return first few lines of CSV."""
        try:
            lines = self._file_path_full.read_text().splitlines()[:20]
            return '\n'.join(lines)
        except Exception:
            return f"-- seed: {self.name}"

    @property
    def file_path_full(self) -> Path:
        return self._file_path_full

    @property
    def file_path_relative(self) -> Path:
        return self._file_path_full.relative_to(self.project.root_folder)

    @property
    def file_name(self) -> str:
        return self._file_path_full.name

    @property
    def parents(self) -> Iterable[DbtEntityAbstract]:
        """Seeds have no incoming dependencies."""
        return []

    @property
    def children(self) -> Iterable[DbtEntityAbstract]:
        """Return entities that depend on this seed."""
        return sorted(list(self.project.graph.successors(self)), key=lambda n: n.name)
