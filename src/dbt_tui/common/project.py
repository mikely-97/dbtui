"""
Abstract base class for dbt projects.

Defines the interface for project operations, entity management,
and graph operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from .entity import DbtEntityAbstract, EntityType
from .model import DbtModelAbstract


class DbtProjectAbstract(ABC):
    """
    Abstract base class for dbt projects.

    A project contains entities (models, seeds, macros, etc.) and provides
    methods for searching, loading, and managing them.
    """

    @abstractmethod
    def __init__(self, project_path: Path | str):
        """Initialize a project from a path."""
        ...

    # =========================================================================
    # Entity-generic methods (for future extensibility)
    # =========================================================================

    @abstractmethod
    def get_entity_by_name(
        self,
        name: str,
        entity_type: EntityType | None = None
    ) -> DbtEntityAbstract:
        """
        Get an entity by name, optionally filtering by type.

        Args:
            name: The entity name to look up
            entity_type: If provided, only search entities of this type

        Returns:
            The matching entity

        Raises:
            Exception if entity not found
        """
        ...

    @abstractmethod
    def search_entities(
        self,
        query: str,
        entity_type: EntityType | None = None
    ) -> Iterable[DbtEntityAbstract]:
        """
        Search for entities matching a query.

        Args:
            query: Search query (supports fuzzy matching, globs, etc.)
            entity_type: If provided, only search entities of this type

        Returns:
            Iterable of matching entities
        """
        ...

    # =========================================================================
    # Model-specific methods (backward compatibility)
    # =========================================================================

    @abstractmethod
    def search_model(self, query: str) -> Iterable[DbtModelAbstract]:
        """Search for models matching a query."""
        ...

    @abstractmethod
    def get_model_by_file_name(self, file_name: str) -> DbtModelAbstract:
        """Get a model by its filename."""
        ...

    @abstractmethod
    def get_model_by_name(self, name: str) -> DbtModelAbstract:
        """Get a model by its name."""
        ...

    @abstractmethod
    def get_model_folders(self) -> list[Path]:
        """Get all folders containing models."""
        ...

    @abstractmethod
    def create_new_model(
        self,
        filepath: Path,
        from_: DbtModelAbstract | None = None
    ) -> DbtModelAbstract:
        """Create a new model at the given path."""
        ...

    # =========================================================================
    # Project operations
    # =========================================================================

    @abstractmethod
    def refresh(self) -> None:
        """Reload the project from disk."""
        ...

