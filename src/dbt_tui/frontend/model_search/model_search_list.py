from ..common import ModelList, ModelListItem
from textual.widgets import ListView, TextArea


class ModelSearchList(ModelList):

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        list_item = event.item
        if not isinstance(list_item, ModelListItem):
            return
        model_preview = self.screen.get_widget_by_id('model_preview')
        assert isinstance(model_preview, TextArea)
        model_preview.clear()
        model_preview.text = list_item.dbt_entity.text
