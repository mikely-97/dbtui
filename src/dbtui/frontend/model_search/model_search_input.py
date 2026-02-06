from ..common import DbtProject
from .model_search_list import ModelSearchList
from textual.widgets import Input
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..main import dbtuiFrontend


class ModelSearchInput(Input):

    app: 'dbtuiFrontend'
    
    def on_input_changed(self, message: Input.Changed):
        assert isinstance(self.app.project, DbtProject)
        models = self.app.project.search_model(message.value)
        model_list = self.screen.get_widget_by_id('model_list')
        assert isinstance(model_list, ModelSearchList)
        model_list.populate_with_models(models=models)

