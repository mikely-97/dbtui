from textual.containers import VerticalGroup
from textual.widgets import Label, ListItem, Rule

from ...common.entity import DbtEntityAbstract


class ModelListItem(ListItem):

    dbt_entity: DbtEntityAbstract

    def __init__(self, model: DbtEntityAbstract, **kwargs):
        entity_type = model.entity_type
        name_label = model.name if entity_type == "model" else f"[{entity_type}] {model.name}"

        # Add dependency count badges for entities that have graph access
        try:
            if hasattr(model, 'project') and model.project and hasattr(model.project, 'graph'):
                parents = list(model.project.graph.predecessors(model))
                children = list(model.project.graph.successors(model))
                if parents or children:
                    badge = f"  ↑{len(parents)} ↓{len(children)}"
                    name_label += badge
        except Exception:
            # If graph access fails, just show the name without badges
            pass

        super().__init__(
            VerticalGroup(
                Label(name_label),
                Rule(),
                Label(str(model.file_path_relative)),
            ),
            **kwargs
        )
        self.dbt_entity = model

    @property
    def dbt_model(self) -> DbtEntityAbstract:
        """Backward-compatible alias for dbt_entity."""
        return self.dbt_entity
