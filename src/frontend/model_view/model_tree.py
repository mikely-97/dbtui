from typing import TYPE_CHECKING

from textual.widgets import Footer, TextArea
from textual.containers import HorizontalGroup, ScrollableContainer
from textual.binding import Binding

from ..common import DbtuiScreen, DbtModel, DbtProject
if TYPE_CHECKING:
    from ..main import dbtuiFrontend

from .parents_list import ParentsList
from .children_list import ChildrenList
from .constants import PARENTS_ID, CHILDREN_ID


class ModelView(DbtuiScreen):
    """Note: This class is unused - ModelTree from model_tree/ is the active implementation."""

    app: 'dbtuiFrontend'

    BINDINGS = [
        Binding("E", "external_edit()", "edit externally",),
        Binding("n", "app.push_screen('new_model')", "new model from current",),
        Binding("enter", "toggle_edit_mode()", "edit", show=False),
        Binding("escape", "exit_edit_mode()", "stop editing", show=False),
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
                        read_only=True,
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

    def action_toggle_edit_mode(self):
        """Enter edit mode when pressing Enter on the TextArea."""
        textarea = self.query_one('#model_content', TextArea)
        if textarea.read_only and textarea.has_focus:
            textarea.read_only = False
            self.app.notify("Editing mode - press Escape to save and exit")

    def action_exit_edit_mode(self):
        """Exit edit mode and save changes when pressing Escape."""
        textarea = self.query_one('#model_content', TextArea)
        if not textarea.read_only:
            textarea.read_only = True
            if self.app.model:
                self.app.model.file_path_full.write_text(textarea.text)
                self.app.notify("Changes saved")
            textarea.blur()
    
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

    def on_project_change(self, project: DbtProject | None):
        if project:
            self.app.push_screen('model_search')

    def on_mount(self):
        self.on_model_change(self.app.model)

