from os.path import exists
from typing import TYPE_CHECKING, Literal
from pathlib import Path



from textual import widgets, containers, reactive, binding
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from .select_filepath import SelectFilepath


from ..common import DbtModel, DbtProject

if TYPE_CHECKING:
    from ..main import dbtuiFrontend



class NewModel(ModalScreen):


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
        # it's supposed to be due to a successful model creation
        self.dismiss()
    
    def on_project_change(self, project: DbtProject|None):
        # we don't care here
        pass
