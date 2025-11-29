from os.path import exists
from typing import TYPE_CHECKING
from pathlib import Path



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



class ProjectSearch(DbtuiScreen):

    @property
    def project_path(self) -> Path:
        if isinstance(self.app.project, DbtProject):
            return self.app.project.root_folder
        else:
            return Path.home()

    def compose(self):

        
        
        yield containers.VerticalScroll(
            widgets.DirectoryTree(
                path=self.project_path,
                name='Select project.yml',
                id='directory_selector',
            ),
            widgets.Input(
                value=self.project_path,
            )
        )
    
    
    def on_model_change(self, model: DbtModel|None):
        # we don't care here
        pass
    
    def on_project_change(self, project: DbtProject|None):

        self.recompose()
