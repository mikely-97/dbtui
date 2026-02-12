from typing import TYPE_CHECKING, Iterable
from textual.widgets import ListView
from textual.binding import Binding
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

    def populate_with_models(self, models: Iterable[DbtModel]):
        self.clear()
        for model in models:
            self.append(
                ModelListItem(
                    model=model
                )
            )
        # we want to instantly focus on the first index
        self.index = None
        self.action_cursor_down()
        # ensure the highlighted item is visible in the viewport
        if self.highlighted_child is not None:
            self.scroll_to_widget(self.highlighted_child)
        
        
    def change_model(self, model: DbtModel):
        # triggers the reactive component
        self.app.model = model
        

    def on_list_view_selected(self, event: ListView.Selected) -> None: 
        list_item: ModelListItem = event.item 
        dbt_model = list_item.dbt_model
        assert isinstance(dbt_model, DbtModel)
        self.change_model(dbt_model)
