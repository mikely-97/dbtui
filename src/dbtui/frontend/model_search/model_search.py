from typing import TYPE_CHECKING

from textual import widgets, containers

from .model_search_input import ModelSearchInput
from .model_search_list import ModelSearchList

from ..common import DbtProject, DbtModel, DbtuiScreen
if TYPE_CHECKING:
    from ..main import dbtuiFrontend


class ModelSearch(DbtuiScreen):

    app: 'dbtuiFrontend'

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
