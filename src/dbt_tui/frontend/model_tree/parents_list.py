from textual.binding import Binding

from ..common import DbtModel, ModelListItem
from .constants import PARENTS_ID, CHILDREN_ID
from .model_relatives_list import ModelRelativesList


class ParentsList(ModelRelativesList):

    BINDINGS =  [
        Binding("left, h", "quick_move()", "select parent",),
        Binding("right, l", "refocus_on_children()", "focus on children",),
    ]

    def on_mount(self):
        assert self.id == PARENTS_ID

    def on_model_change(self, model: DbtModel):
        super().on_model_change(model)

    def action_quick_move(self) -> None:
        if self.highlighted_child:
            assert(isinstance(self.highlighted_child, ModelListItem))
            entity = self.highlighted_child.dbt_entity
            if entity.entity_type == 'model':
                self.change_model(entity)  # type: ignore[arg-type]
            else:
                self.app.notify(f"Cannot navigate to {entity.entity_type} '{entity.name}'")

    def action_refocus_on_children(self) -> None:
        chidlren = self.screen.get_widget_by_id(CHILDREN_ID)
        chidlren.focus()
