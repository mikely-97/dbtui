from typing import TYPE_CHECKING

from textual.widgets import Footer, TextArea
from textual.containers import HorizontalGroup, ScrollableContainer
from textual.binding import Binding
from textual.events import Key

from ..common import DbtuiScreen, DbtModel, DbtProject
from ..common.timing import TimingContext
if TYPE_CHECKING:
    from ..main import dbtuiFrontend

from .parents_list import ParentsList
from .children_list import ChildrenList
from .constants import PARENTS_ID, CHILDREN_ID


class ModelTree(DbtuiScreen):

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
            # Save changes to the model file
            if self.app.model:
                self.app.model.file_path_full.write_text(textarea.text)
                self.app.notify("Changes saved")
            textarea.blur()
    
    def on_model_change(self, model: DbtModel|None):
        if not model:
            self.app.push_screen('model_search')
            return

        timing = TimingContext("ModelTree.on_model_change")

        # model_content
        with timing.step("get_widget(model_content)"):
            model_content = self.get_widget_by_id('model_content')
        assert isinstance(model_content, TextArea)

        with timing.step("model_content.clear"):
            model_content.clear()

        with timing.step("model.text (file read)"):
            text = model.text

        with timing.step("model_content.load_text"):
            model_content.load_text(text)

        # parents
        with timing.step("get_widget(parents)"):
            parents = self.get_widget_by_id('parents')
        assert isinstance(parents, ParentsList)

        with timing.step("parents.on_model_change"):
            parents.on_model_change(model)

        # children
        with timing.step("get_widget(children)"):
            children = self.get_widget_by_id('children')
        assert isinstance(children, ChildrenList)

        with timing.step("children.on_model_change"):
            children.on_model_change(model)

        # Note: recompose() removed - unnecessary since:
        # - TextArea is updated via load_text()
        # - ListViews are updated via clear() and append()

        timing.log()

    def on_project_change(self, project: DbtProject | None):
        # When project changes, redirect to model search
        if project:
            self.app.push_screen('model_search')

    def on_mount(self):
        self.on_model_change(self.app.model)

