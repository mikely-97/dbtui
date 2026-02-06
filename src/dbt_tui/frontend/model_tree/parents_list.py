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
        self.populate_with_models(model.parents)
    
    def action_quick_move(self) -> None:
        if self.highlighted_child:
            assert(isinstance(self.highlighted_child, ModelListItem))
            self.change_model(self.highlighted_child.dbt_model)
    
    def action_refocus_on_children(self) -> None:
        chidlren = self.screen.get_widget_by_id(CHILDREN_ID)
        chidlren.focus()