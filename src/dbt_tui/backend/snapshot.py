"""Snapshot entity representing a dbt snapshot."""
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from dbt_tui.common.entity import DbtEntityAbstract, EntityType

if TYPE_CHECKING:
    from .project import DbtProject


class DbtSnapshot(DbtEntityAbstract):
    """Represents a dbt snapshot (SQL file tracking historical changes)."""

    _file_path_full: Path
    _text: str
    project: 'DbtProject'

    def __init__(self, file_path: Path, project: 'DbtProject'):
        self._file_path_full = file_path
        self.project = project
        with open(file_path, encoding='utf-8') as f:
            self._text = f.read()

    @property
    def name(self) -> str:
        return self._file_path_full.stem

    @property
    def entity_type(self) -> EntityType:
        return "snapshot"

    @property
    def text(self) -> str:
        return self._text

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
        """Snapshots may have dependencies via refs and sources."""
        return sorted(list(self.project.graph.predecessors(self)), key=lambda n: n.name)

    @property
    def children(self) -> Iterable[DbtEntityAbstract]:
        """Return entities that depend on this snapshot."""
        return sorted(list(self.project.graph.successors(self)), key=lambda n: n.name)
