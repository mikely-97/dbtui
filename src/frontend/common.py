from os.path import exists

from typing import Iterable

from textual import widgets, containers

isolated = exists('.isolated')
if isolated:
    from .pseudo import DbtModel
else:
    from ..backend.project import DbtModel

class ModelListItem(widgets.ListItem):

    dbt_model: DbtModel

    def __init__(self, model: DbtModel, **kwargs):

        super().__init__(
            containers.VerticalGroup(
                widgets.Label(model.name),
                widgets.Rule(),
                widgets.Label(str(model.file_path_relative)),
            ),
            **kwargs
        )
        self.dbt_model = model
    
    def become_active(self):
        self.app.

    

class ModelList(widgets.ListView):

    def populate_with_models(self, models: Iterable[DbtModel]):
        self.clear()
        for model in models:
            self.append(
                ModelListItem(
                    model=model
                )
            )
        
    
    def on_list_view_selected(self, event: widgets.ListView.Selected) -> None: 
        list_item: ModelListItem = event.item 
        dbt_model = list_item.dbt_model
        assert isinstance(dbt_model, DbtModel)
        self.app.ctx.active_model = dbt_model
        self.screen.on_model_change()
