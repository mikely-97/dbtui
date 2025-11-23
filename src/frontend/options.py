from os.path import exists
from typing import TYPE_CHECKING

from textual import widgets, containers, screen

from src.backend.project import DbtProject
from src.frontend.pseudo import DbtProject

from .common import ModelList, ModelListItem, DbtuiScreen
if TYPE_CHECKING:
    from .main import dbtuiFrontend


isolated = exists('.isolated')
if isolated:
    from .pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel

class ExternalEditorOption(widgets.Input):

    app: 'dbtuiFrontend'

    def on_input_submitted(self, event: widgets.Input.Submitted):
        self.app.external_editor_command = event.value



class Options(DbtuiScreen):

    def compose(self):
        
        yield containers.VerticalScroll(
            ExternalEditorOption(
                value=self.app.external_editor_command
            )   
        )
    
    
    def on_model_change(self, model: DbtModel|None):
        # we don't care here
        pass
    
    def on_project_change(self, project: DbtProject|None):
        # we don't care here
        pass
