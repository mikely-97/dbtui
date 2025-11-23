from os.path import exists
from typing import Literal, TYPE_CHECKING

from textual import widgets, containers, screen
from textual.binding import Binding

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
    
    def on_list_view_highlighted(self, event: widgets.ListView.Highlighted) -> None:
        list_item: ModelListItem = event.item
        pass 

    def on_model_change(self, model: DbtModel):
        if self.id == 'parents':
            self.populate_with_models(model.parents)
        elif self.id == 'children':
            self.populate_with_models(model.children)
        else:
            raise NotImplementedError
    
    def on_key_left(self) -> None:
        if self.id == 'parents' and self.highlighted_child:
            assert(isinstance(self.highlighted_child, ModelListItem))
            self.app.change_model(self.highlighted_child.dbt_model)


class ParentsList(ModelRelativesList):

    BINDINGS = [
        Binding("left", "quick_move()", "select parent",),
        Binding("h", "quick_move()", "select parent",),
        Binding("right", "refocus_on_children()", "focus on children",),
        Binding("l", "refocus_on_children()", "focus on children",),
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
        Binding("right", "quick_move()", "select child",),
        Binding("l", "quick_move()", "select child",),
        Binding("left", "refocus_on_parents()", "focus on parents",),
        Binding("h", "refocus_on_parents()", "focus on parents",),
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

    


class ModelView(DbtuiScreen):


    BINDINGS = [
        # ("O", "options", "open options"),
        ("f", "push_screen('model_search')", "search models"),
    ]

    def compose(self):
        yield containers.HorizontalGroup(
            ParentsList(
                id=PARENTS_ID,
                name='model_parents',
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

    def on_mount(self):
        self.on_model_change(self.app.model)   

