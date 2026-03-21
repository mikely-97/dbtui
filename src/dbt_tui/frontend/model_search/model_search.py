from typing import TYPE_CHECKING

from textual import widgets, containers
from textual.binding import Binding
from textual.widgets import Checkbox

from .model_search_input import ModelSearchInput
from .model_search_list import ModelSearchList

from ..common import DbtProject, DbtModel, DbtTuiScreen
if TYPE_CHECKING:
    from ..main import DbtTuiFrontend


class ModelSearch(DbtTuiScreen):

    app: 'DbtTuiFrontend'

    BINDINGS = [
        Binding("escape", "go_back", "back", show=True),
    ]

    def compose(self):

        yield containers.Horizontal(
            Checkbox("Models", value=True, id="filter-models"),
            Checkbox("Macros", value=True, id="filter-macros"),
            id='search-filters'
        )
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
        # Redirect to project_search if no project is loaded
        if self.app.project is None:
            self.app.push_screen('project_search')
            return
        self._focus_search_input()

    def _focus_search_input(self):
        """Set focus to the search input."""
        try:
            self.app.set_focus(self.get_widget_by_id('search_input'))
        except Exception:
            pass  # Widget may not exist yet

    def action_go_back(self):
        """Go back to model_view if there's an active model, otherwise pop screen."""
        if self.app.has_active_model:
            self.app.push_screen('model_view')
        else:
            self.app.pop_screen()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Re-run search when a filter checkbox is toggled."""
        try:
            search_input = self.get_widget_by_id('search_input')
            from .model_search_input import ModelSearchInput
            assert isinstance(search_input, ModelSearchInput)
            search_input._do_search(search_input.value)
        except Exception:
            pass

    def on_model_change(self, model: DbtModel|None):
        # reset the search and its results
        self.compose()
        self._focus_search_input()

    def on_project_change(self, project: DbtProject|None):
        # Redirect to project_search if project becomes None
        if project is None:
            self.app.push_screen('project_search')
            return
        # reset the search and its results
        self.compose()
        self._focus_search_input()
