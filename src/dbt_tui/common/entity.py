"""
Base entity abstraction for dbt resources.

This module defines the abstract base class for all dbt entities (models, seeds, macros, etc.).
Entity-specific behavior should be implemented in subclasses.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Literal

if TYPE_CHECKING:
    from .project import DbtProjectAbstract


EntityType = Literal["model", "seed", "macro", "snapshot", "analysis"]


class DbtEntityAbstract(ABC):
    """
    Abstract base class for all dbt entities.

    Entities are the core resources in a dbt project: models, seeds, macros,
    snapshots, and analyses. This class defines the common interface shared
    by all entity types.
    """

    @property
    @abstractmethod
    def entity_type(self) -> EntityType:
        """Return the type of this entity (model, seed, macro, etc.)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this entity."""
        ...

    @property
    @abstractmethod
    def text(self) -> str:
        """Return the text content of this entity's file."""
        ...

    @property
    @abstractmethod
    def file_path_full(self) -> Path:
        """Return the absolute path to this entity's file."""
        ...

    @property
    @abstractmethod
    def file_path_relative(self) -> Path:
        """Return the path relative to the project root."""
        ...

    @property
    @abstractmethod
    def file_name(self) -> str:
        """Return just the filename (with extension)."""
        ...

    @property
    @abstractmethod
    def parents(self) -> Iterable['DbtEntityAbstract']:
        """Return entities that this entity depends on."""
        ...

    @property
    @abstractmethod
    def children(self) -> Iterable['DbtEntityAbstract']:
        """Return entities that depend on this entity."""
        ...

    @property
    def file_extension(self) -> str:
        """Return the file extension (e.g., '.sql', '.csv')."""
        return self.file_path_full.suffix
