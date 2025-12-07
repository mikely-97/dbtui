from typing import TYPE_CHECKING, Literal
from pathlib import Path

from textual import widgets, containers, reactive, binding

from src.backend.project import DbtProject, DbtModel

from ..common import DbtuiScreen
if TYPE_CHECKING:
    from ..main import dbtuiFrontend


class DirectorySelector(widgets.DirectoryTree):

    screen: 'ProjectSearch'

    def on_directory_tree_directory_selected(self, event: widgets.DirectoryTree.DirectorySelected):
        # isn't the best way, but tbh im not making a fs explorer
        if Path.exists(event.path/'dbt_project.yml'):
            self.screen.project_path = event.path

class DirectoryInput(widgets.Input):

    screen: 'ProjectSearch'

    def on_input_submitted(self, event: widgets.Input.Submitted):
        self.screen.project_path = event.value


class ProjectSearch(DbtuiScreen):

    """
    we're not making a fs explorer here, but in case you need to look up another dbt project - here you go
    i basically think it would be the best option to launch a project as `dbtui path/to/project`
    but i leave an option to select with directory input or manual input inside the app
    """

    app: 'dbtuiFrontend'

    # only add it if we actually have an active project
    active_project_binding = binding.Binding("p", "reset_path('active_project')", "to active_project"),

    BINDINGS = [
        binding.Binding("h", "reset_path('home')", "to home dir"),
    ]

    project_path: reactive.reactive[Path] = reactive.reactive(Path.home())

    def validate_project_path(self, value: str|Path) -> Path:
        new_project_path = Path(value)
        if new_project_path.exists():
            return new_project_path
        if not new_project_path.exists():
            self.notify("Path doesn't exist")
            return self.project_path
    
    def watch_project_path(self, old_value: Path, new_value: Path):
        if old_value == new_value: # meaning it wasn't validated
            return 

        try:
            self.app.project = DbtProject(new_value)
        except FileNotFoundError as e:
            self.notify(e.args[0])
            return


    def action_reset_path(self, to=Literal['home', 'active_project']):
        default = Path.home()
        if not self.app.has_active_project:
            return default
        match to:
            case 'active_project':
                self.project_path = self.app.project.root_folder
            case 'home':
                self.project_path = default 
            case _:
                raise NotImplementedError("Unknown argument to reset_path: %s" % to)

    def compose(self):

        yield containers.VerticalScroll(
            DirectorySelector(
                path=Path.home(),
                name='Select project.yml',
                id='directory_selector',
            ),
            DirectoryInput(
                id='directory_input',
            ),
            widgets.Footer(),
        )

        self.action_reset_path('active_project')
    
    
    def on_model_change(self, model: DbtModel|None):
        # we don't care here
        pass
    
    def on_project_change(self, project: DbtProject|None):
        dir_selector = self.get_widget_by_id('directory_selector')
        assert isinstance(dir_selector, DirectorySelector)
        dir_selector.path = project.root_folder
        dir_input = self.get_widget_by_id('directory_input')
        assert isinstance(dir_input, DirectoryInput)
        if not dir_input.has_focus:
            dir_input.value = project.root_folder.as_posix()

        if not self.active_project_binding in self.BINDINGS:
            self.BINDINGS.append(self.active_project_binding)
