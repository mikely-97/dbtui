from textual.containers import VerticalGroup
from textual.widgets import Label, ListItem, Rule

from ...common.entity import DbtEntityAbstract


class ModelListItem(ListItem):

    dbt_entity: DbtEntityAbstract

    def __init__(self, model: DbtEntityAbstract, **kwargs):
        entity_type = model.entity_type
        name_label = model.name if entity_type == "model" else f"[{entity_type}] {model.name}"

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
