from typing import TYPE_CHECKING, Iterable
from textual.widgets import ListView
from textual.binding import Binding
from .isolated import DbtModel
from .model_list_item import ModelListItem

if TYPE_CHECKING:
    from ..main import dbtuiFrontend

class ModelList(ListView):

    BINDINGS =  [
        Binding("j", "cursor_down()", show=False),
        Binding("k", "cursor_up()", show=True,),
    ]

    app: 'dbtuiFrontend'

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
        # TODO: when tampering with CSS, check out how u can fix the invisible highlight
        
        
    def change_model(self, model: DbtModel):
        # triggers the reactive component
        self.app.model = model
        

    def on_list_view_selected(self, event: ListView.Selected) -> None: 
        list_item: ModelListItem = event.item 
        dbt_model = list_item.dbt_model
        assert isinstance(dbt_model, DbtModel)
        self.change_model(dbt_model)
