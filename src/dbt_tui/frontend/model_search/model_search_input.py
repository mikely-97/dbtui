from .model_search_list import ModelSearchList
from textual.widgets import Input, Checkbox
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
        try:
            cb_models = self.screen.get_widget_by_id('filter-models')
            cb_macros = self.screen.get_widget_by_id('filter-macros')
            if not isinstance(cb_models, Checkbox):
                return
            if not isinstance(cb_macros, Checkbox):
                return
            want_models = cb_models.value
            want_macros = cb_macros.value
        except Exception:
            want_models = True
            want_macros = True

        model_list = self.screen.get_widget_by_id('model_list')
        if not isinstance(model_list, ModelSearchList):
            return

        if not want_models and not want_macros:
            model_list.populate_with_entities(entities=[])
            return

        if want_models and want_macros:
            entity_type = None
        elif want_models:
            entity_type = 'model'
        else:
            entity_type = 'macro'

        try:
            tag_input = self.screen.get_widget_by_id('filter-tag')
            tag = tag_input.value.strip() if hasattr(tag_input, 'value') else None
            tag = tag or None
        except Exception:
            tag = None

        try:
            mat_input = self.screen.get_widget_by_id('filter-mat')
            mat = mat_input.value.strip() if hasattr(mat_input, 'value') else None
            mat = mat or None
        except Exception:
            mat = None

        entities = self.app.project.search_entities(value, entity_type=entity_type, tag=tag, materialized=mat)
        model_list.populate_with_entities(entities=entities)

    def on_input_changed(self, message: Input.Changed) -> None:
        self._do_search(message.value)

