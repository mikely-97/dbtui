
from os.path import exists
from pathlib import Path
from dataclasses import dataclass

from textual.app import App 
from textual.binding import Binding
from textual.reactive import reactive
from typing import Any 

isolated = exists('.isolated')

if isolated:
    from .pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel

from .model_search.model_search import ModelSearch
from .model_tree import ModelTree
from .options import Options
from .project_search import ProjectSearch

from ..common import dbtuiCache, load_cache, save_cache, NonePathException
from .common import DbtuiScreen
import logging

@dataclass
class AppContext:
    project: DbtProject|None = None
    model: DbtModel|None = None



class dbtuiFrontend(App):

    BINDINGS = [
        ("o", "push_screen('options')", "open options"),
        ("f", "push_screen('model_search')", "search models"),
        ("p", "push_screen('project_search')", "select project"),

    ]

    SCREENS = {
        'model_search': ModelSearch,
        'model_view': ModelTree,
        'options': Options,
        'project_search': ProjectSearch,
        }

    screen_stack: list[DbtuiScreen]
    external_editor_command: reactive[str] = reactive('vi')

    def watch_external_editor_command(self, old_value: str, new_value: str):
        self.save_context()

    # TODO: decompose into mixins
    model: reactive[DbtProject|None] = reactive(None, always_update=True, init=True)

    def validate_project(self, project: Any) -> DbtProject|None:
        if not isinstance(project, DbtProject):
            return None 
        return DbtProject
    
    def on_project_change(self, project: DbtProject|None):
        self.save_context()
        for screen in self.screen_stack:
            # TODO: inherit screens from an ABC with on_project_change
            screen.on_project_change()
        pass
    
    def watch_project(self, old_project: DbtProject|None, new_project: DbtProject|None):
        self.on_project_change(new_project)

    model: reactive[DbtModel|None] = reactive(None, always_update=True, init=True)


    def validate_model(self, model: Any) -> DbtModel|None:
        if not isinstance(model, DbtModel):
            return None 
        return model
    
    def on_model_change(self, model: DbtModel|None):
        self.save_context()
        for screen in self.screen_stack:
            if not screen.id == '_default':
                screen.on_model_change(model)
        self.push_screen('model_view')
        pass
    
    def watch_model(self, old_model: DbtModel|None, new_model: DbtModel|None):
        
        self.on_model_change(new_model)

    @property
    def has_active_model(self) -> bool:
        if isinstance(self.model, DbtModel):
            return True
        return False
    
    @property
    def has_active_project(self) -> bool:
        if isinstance(self.project, DbtProject):
            return True
        return False
        

    def load_context(self, clear_cache: bool=False):
        cache: dbtuiCache = load_cache(clear_cache)
        project = None
        model = None
        try:
            project = DbtProject(project_path=cache.last_open_project)
        except NonePathException:
            pass # that means we don't have anything saved, so don't log anything
        except Exception as e:
            logging.warn(f"Failed to load project {cache.last_open_project} for reason: {e.args}")
        if project is not None:
            try:
                model = project.get_model_by_name(cache.last_active_model)
            except Exception as e:
                logging.warn(e.args)
        self.project = project 
        self.model = model
        self.external_editor_command = cache.external_editor_command
        
    def save_context(self):
        save_cache(
            project_path=self.project.root_folder if isinstance(self.project, DbtProject) else None,
            model_name=self.model.name if isinstance(self.model, DbtModel) else None,
            external_editor_command=self.external_editor_command,
        )
    

    def on_mount(self):
        self.load_context()
        if self.project is None:
            # we will open a screen to select the folder
            # but for now we default to the testing project
            # TODO
            self.project = DbtProject(project_path=Path('tests/testing'))
        if self.model is None:
            self.push_screen('model_search')
        else:
            self.push_screen('model_view')
    


if __name__ == '__main__':

    dbtui_front = dbtuiFrontend()
    dbtuiFrontend().run()
