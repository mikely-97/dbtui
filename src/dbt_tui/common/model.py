"""
Model-specific abstract class for dbt models.

DbtModelAbstract extends DbtEntityAbstract with model-specific behavior
like ref() parsing and configuration.
"""

from abc import abstractmethod

from .entity import DbtEntityAbstract, EntityType


class DbtModelAbstract(DbtEntityAbstract):
    """
    Abstract base class for dbt models.

    Models are SQL files that define transformations. They can reference
    other models via ref() and have configurations via config().
    """

    @property
    def entity_type(self) -> EntityType:
        """Models always return 'model' as their entity type."""
        return "model"

    @property
    @abstractmethod
    def refs(self) -> list[str]:
        """Return list of model names referenced via ref()."""
        ...

