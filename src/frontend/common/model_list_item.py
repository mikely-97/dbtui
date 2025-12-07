from textual.widgets import ListItem, Label, Rule
from textual.containers import VerticalGroup
from .isolated import DbtModel


class ModelListItem(ListItem):

    dbt_model: DbtModel

    def __init__(self, model: DbtModel, **kwargs):

        super().__init__(
            VerticalGroup(
                Label(model.name),
                Rule(),
                Label(str(model.file_path_relative)),
            ),
            **kwargs
        )
        self.dbt_model = model
