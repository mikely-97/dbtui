from typing import Iterable

from textual import widgets, containers

isolated = True
if isolated:
    from pseudo import DbtModel
else:
    from ..backend.project import DbtModel

class ModelListItem(widgets.ListItem):

    dbt_model: DbtModel

    def __init__(self, model: DbtModel, **kwargs):

        super().__init__(
            containers.VerticalGroup(
                widgets.Label(model.name),
                widgets.Rule(),
                widgets.Label(model.filepath),
            ),
            **kwargs
        )
        self.dbt_model = model
    

class ModelList(widgets.ListView):

    def populate_with_models(self, models: Iterable[DbtModel]):
        self.clear()
        for model in models:
            self.append(
                ModelListItem(
                    model=model
                )
            )
