from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from ..common.entity import DbtEntityAbstract
from ..common.macro import DbtMacroAbstract

if TYPE_CHECKING:
    from .project import DbtProject


class DbtMacro(DbtMacroAbstract):
    _file_path_full: Path
    _text: str
    project: 'DbtProject'

    def __init__(self, file_path_full: Path, project: 'DbtProject'):
        self._file_path_full = file_path_full
        self.project = project
        with open(file_path_full, encoding='utf-8') as f:
            self._text = f.read()

    @property
    def name(self) -> str:
        return self._file_path_full.stem

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
        return []

    @property
    def children(self) -> Iterable[DbtEntityAbstract]:
        return sorted(list(self.project.graph.successors(self)), key=lambda n: n.name)
