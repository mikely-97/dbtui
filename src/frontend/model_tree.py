from os.path import exists
from typing import Literal, TYPE_CHECKING
import os 

from textual import events, widgets, containers, screen
from textual.binding import Binding
from textual.events import Mount

from .common import ModelList, ModelListItem, DbtuiScreen
if TYPE_CHECKING:
    from .main import dbtuiFrontend

isolated = exists('.isolated')
if isolated:
    from .pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel

CHILDREN_ID = 'children'
PARENTS_ID = 'parents'


class ModelRelativesList(ModelList):

    id: Literal['parents', 'children']
    
    def on_model_change(self, model: DbtModel):
        if self.id == PARENTS_ID:
            self.populate_with_models(model.parents)
        elif self.id == CHILDREN_ID:
            self.populate_with_models(model.children)
        else:
            raise NotImplementedError

    


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

    


class ModelTree(DbtuiScreen):

    BINDINGS = [
        Binding("E", "external_edit()", "edit externally",),
    ]


    def compose(self):
        yield containers.HorizontalGroup(
            ParentsList(
                id=PARENTS_ID,
                name='model_parents',
                initial_index=1,
            ),
            containers.ScrollableContainer(
                    widgets.TextArea(
                        id='model_content',
                        name='content',
                        read_only=True, # TODO: not read-only when pressing Enter, back to read-only when pressing Esc 
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
            
        yield widgets.Footer()
    
    def on_model_change(self, model: DbtModel|None):
        if not model:
            self.app.push_screen('model_search')
            return
        # model_content
        model_content = self.get_widget_by_id('model_content')
        assert isinstance(model_content, widgets.TextArea)
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

