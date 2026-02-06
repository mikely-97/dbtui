from textual.binding import Binding

from ..common import DbtModel, ModelListItem
from .constants import PARENTS_ID, CHILDREN_ID
from .model_relatives_list import ModelRelativesList


class ChildrenList(ModelRelativesList):

    BINDINGS = [
        Binding("right, l", "quick_move()", "select child",),
        Binding("left, h", "refocus_on_parents()", "focus on parents",),
    ]

    def on_mount(self):
        assert self.id == CHILDREN_ID

    def on_model_change(self, model: DbtModel):
        self.populate_with_models(model.children)
    
    def action_quick_move(self) -> None:
        if self.highlighted_child:
            assert(isinstance(self.highlighted_child, ModelListItem))
            self.change_model(self.highlighted_child.dbt_model)
    
    def action_refocus_on_parents(self) -> None:
        parents = self.screen.get_widget_by_id(PARENTS_ID)
        parents.focus()
