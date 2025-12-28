from typing import TYPE_CHECKING

from textual.widgets import Footer, TextArea
from textual.containers import HorizontalGroup, ScrollableContainer
from textual.binding import Binding

from ..common import DbtuiScreen, DbtModel
if TYPE_CHECKING:
    from ..main import dbtuiFrontend

from .parents_list import ParentsList
from .children_list import ChildrenList
from .constants import PARENTS_ID, CHILDREN_ID


class ModelView(DbtuiScreen):

    app: 'dbtuiFrontend'

    BINDINGS = [
        Binding("E", "external_edit()", "edit externally",),
        Binding("n", "app.push_screen('new_model')", "new model from current",),
    ]


    def compose(self):
        yield HorizontalGroup(
            ParentsList(
                id=PARENTS_ID,
                name='model_parents',
                initial_index=1,
            ),
            ScrollableContainer(
                    TextArea(
                        id='model_content',
                        name='content',
                        read_only=False, # TODO: not read-only when pressing Enter, back to read-only when pressing Esc 
                        show_line_numbers=True,
                        language='sql',
                )
            ),
            ChildrenList(
                id=CHILDREN_ID,
                name='model children',
                initial_index=1,
            )
        )
            
        yield Footer()
    
    def on_model_change(self, model: DbtModel|None):
        if not model:
            self.app.push_screen('model_search')
            return
        # model_content
        model_content = self.get_widget_by_id('model_content')
        assert isinstance(model_content, TextArea)
        model_content.clear()
        model_content.load_text(model.text)
        # parents
        parents = self.get_widget_by_id('parents')
        assert isinstance(parents, ParentsList)
        parents.on_model_change(model)
        # children
        children = self.get_widget_by_id('children')
        assert isinstance(children, ChildrenList)
        children.on_model_change(model)
        self.recompose()

    def on_mount(self):
        self.on_model_change(self.app.model)   

