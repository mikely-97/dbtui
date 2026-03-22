"""Source entity representing a dbt source table."""
from collections.abc import Iterable
from pathlib import Path

from dbt_tui.common.entity import DbtEntityAbstract, EntityType


class DbtSource(DbtEntityAbstract):
    """Represents a dbt source (external data table)."""

    def __init__(self, source_name: str, table_name: str):
        self._source_name = source_name
        self._table_name = table_name

    @property
    def name(self) -> str:
        return f"{self._source_name}.{self._table_name}"

    @property
    def source_name(self) -> str:
        return self._source_name

    @property
    def table_name(self) -> str:
        return self._table_name

    @property
    def entity_type(self) -> EntityType:
        return "source"

    @property
    def text(self) -> str:
        return f"-- source: {self._source_name}.{self._table_name}"

    @property
    def file_path_full(self) -> Path:
        """Return a sensible default path for sources (not actual files)."""
        return Path('/dev/null')

    @property
    def file_path_relative(self) -> Path:
        """Return relative path representation."""
        return Path(f"sources/{self._source_name}/{self._table_name}")

    @property
    def file_name(self) -> str:
        """Return filename representation."""
        return f"{self._table_name}"

    @property
    def parents(self) -> Iterable['DbtEntityAbstract']:
        """Sources have no dependencies."""
        return []

    @property
    def children(self) -> Iterable['DbtEntityAbstract']:
        """Return entities that depend on this source."""
        # This would be populated by the graph in DbtProject
        return []
