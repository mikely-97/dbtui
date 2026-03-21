from .model_search_list import ModelSearchList
from textual.widgets import Input
from textual.events import Key
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..main import DbtTuiFrontend


class ModelSearchInput(Input):

    app: 'DbtTuiFrontend'

    def on_key(self, event: Key) -> None:
        """Forward navigation keys to the model list."""
        model_list = self.screen.get_widget_by_id('model_list')
        if not isinstance(model_list, ModelSearchList):
            return

        # Forward these keys to the list for navigation
        if event.key in ("down", "j"):
            model_list.action_cursor_down()
            event.prevent_default()
            event.stop()
        elif event.key in ("up", "k"):
            model_list.action_cursor_up()
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            # Select the highlighted item in the list
            if model_list.highlighted_child is not None:
                model_list.action_select_cursor()
                event.prevent_default()
                event.stop()

    def _do_search(self, value: str) -> None:
        """Run a search with the given query value, respecting current filter checkboxes."""
        if self.app.project is None:
            return
        from textual.widgets import Checkbox
        try:
            cb_models = self.screen.get_widget_by_id('filter-models')
            cb_macros = self.screen.get_widget_by_id('filter-macros')
            assert isinstance(cb_models, Checkbox)
            assert isinstance(cb_macros, Checkbox)
            want_models = cb_models.value
            want_macros = cb_macros.value
        except Exception:
            want_models = True
            want_macros = True

        if want_models and want_macros:
            entity_type = None
        elif want_models:
            entity_type = 'model'
        elif want_macros:
            entity_type = 'macro'
        else:
            entity_type = None

        entities = self.app.project.search_entities(value, entity_type=entity_type)
        model_list = self.screen.get_widget_by_id('model_list')
        assert isinstance(model_list, ModelSearchList)
        model_list.populate_with_entities(entities=entities)

    def on_input_changed(self, message: Input.Changed) -> None:
        self._do_search(message.value)

