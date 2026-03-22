from collections.abc import Iterable
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.widgets import ListView

from ...common.entity import DbtEntityAbstract
from .isolated import DbtModel
from .model_list_item import ModelListItem

if TYPE_CHECKING:
    from ..main import DbtTuiFrontend

class ModelList(ListView):

    BINDINGS = [
        Binding("down, j", "cursor_down()", show=False),
        Binding("up, k", "cursor_up()", show=False),
    ]

    app: 'DbtTuiFrontend'

    def populate_with_entities(self, entities: Iterable[DbtEntityAbstract]):
        self.clear()
        for entity in entities:
            self.append(
                ModelListItem(
                    model=entity
                )
            )
        # we want to instantly focus on the first index
        self.index = None
        self.action_cursor_down()
        # ensure the highlighted item is visible in the viewport
        if self.highlighted_child is not None:
            self.scroll_to_widget(self.highlighted_child)

    def populate_with_models(self, models: Iterable[DbtModel]):
        """Backward-compatible alias for populate_with_entities."""
        self.populate_with_entities(models)

    def change_model(self, model: DbtModel):
        # triggers the reactive component
        self.app.model = model

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        list_item: ModelListItem = event.item
        entity = list_item.dbt_entity
        if entity.entity_type == 'model':
            self.change_model(entity)  # type: ignore[arg-type]
        else:
            self.app.notify(f"Navigation to {entity.entity_type} '{entity.name}' is not supported")
