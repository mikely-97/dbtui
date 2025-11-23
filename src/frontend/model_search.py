from os.path import exists
from typing import TYPE_CHECKING

from textual import widgets, containers, screen

from src.backend.project import DbtProject
from src.frontend.pseudo import DbtProject

from .common import ModelList, ModelListItem, DbtuiScreen
if TYPE_CHECKING:
    from .main import dbtuiFrontend


isolated = exists('.isolated')
if isolated:
    from .pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel


class ModelSearchList(ModelList):

    def on_list_view_highlighted(self, event: widgets.ListView.Highlighted) -> None:
        list_item = event.item
        if not isinstance(list_item, ModelListItem):
            return
        model_preview = self.screen.get_widget_by_id('model_preview')
        assert isinstance(model_preview, widgets.TextArea)
        model_preview.clear()
        model_preview.text = list_item.dbt_model.text


class ModelSearchInput(widgets.Input):

    app: 'dbtuiFrontend'
    
    def on_input_changed(self, message: widgets.Input.Changed):
        assert isinstance(self.app.project, DbtProject)
        models = self.app.project.search_model(message.value)
        model_list = self.screen.get_widget_by_id('model_list')
        assert isinstance(model_list, ModelSearchList)
        model_list.populate_with_models(models=models)



class ModelSearch(DbtuiScreen):

    BINDINGS = [
        ("O", "options", "open options")
    ]

    def compose(self):
        
        yield containers.Horizontal(
            ModelSearchList(
                id='model_list',
                name='model list'
                ),
            containers.ScrollableContainer(
                widgets.TextArea(
                    id='model_preview',
                    name='preview',
                    read_only=True,
                    show_line_numbers=True,
                    language='sql'
                ),
                id='model_preview_scrollable'
            ),
            id='search_results'
        )
        yield ModelSearchInput(
            id='search_input',
            placeholder='Enter the model name or dbt search string'
        )
    
    def on_mount(self):
        self.app.set_focus(
            self.get_widget_by_id('search_input')
        )
    
    def on_model_change(self, model: DbtModel|None):
        # reset the search and its results
        self.compose()
    
    def on_project_change(self, project: DbtProject|None):
        # reset the search and its results
        self.compose()
