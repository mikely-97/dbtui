"""
Macro-specific abstract class for dbt macros.

DbtMacroAbstract extends DbtEntityAbstract for macro resources.
Macros are Jinja2 files that define reusable SQL/Jinja logic.
"""

from .entity import DbtEntityAbstract, EntityType


class DbtMacroAbstract(DbtEntityAbstract):
    """
    Abstract base class for dbt macros.

    Macros are Jinja2 files in the macro-paths directories.
    They can be called by models and other macros.
    """

    @property
    def entity_type(self) -> EntityType:
        """Macros always return 'macro' as their entity type."""
        return "macro"
