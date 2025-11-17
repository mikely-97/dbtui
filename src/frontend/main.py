
from os.path import exists
from pathlib import Path
from dataclasses import dataclass

from textual.app import App 
from textual import widgets
from typing import Any 

isolated = exists('.isolated')

if isolated:
    from .pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel

from .model_search import ModelSearch
from .model_view import ModelView
from ..common import dbtuiCache, load_cache, save_cache, NonePathException
import logging

@dataclass
class AppContext:
    project: DbtProject|None = None
    active_model: DbtModel|None = None



class dbtuiFrontend(App):

    ctx: AppContext

    BINDINGS = [
        # ("O", "options", "open options"),
        ("f", "push_screen('model_search')", "search models"),

    ]

    SCREENS = {
        'model_search': ModelSearch,
        'model_view': ModelView,
        }
    
    def on_project_loading_failure(self) -> Path:
        
        pass
        

    

    def load_context(self, clear_cache: bool=False):
        cache: dbtuiCache = load_cache(clear_cache)
        project = None
        active_model = None
        try:
            project = DbtProject(project_path=cache.last_open_project)
        except NonePathException:
            pass # that means we don't have anything saved, so don't log anything
        except Exception as e:
            logging.warn(f"Failed to load project {cache.last_open_project} for reason: {e.args}")
        if project is not None:
            try:
                active_model = project.get_model_by_name(cache.last_active_model)
            except Exception as e:
                logging.warn(e.args)
        self.ctx: AppContext = AppContext(
            project=project,
            active_model=active_model,
        )
        
    def save_context(self):
        save_cache(
            project_path=self.ctx.project.root_folder if isinstance(self.ctx.project, DbtProject) else None,
            active_model_name=self.ctx.active_model.name if isinstance(self.ctx.active_model, DbtModel) else None,
        )


    def compose(self):
        assert isolated # TODO: choose the initial screen based on dbtui cache
        yield widgets.Footer()
        # yield ModelSearch(id='model_search')
    

    def on_mount(self):
        self.load_context()
        if self.ctx.project is None:
            # we will open a screen to select the folder
            # but for now we default to the testing project
            # TODO
            self.ctx.project = DbtProject(project_path=Path('tests/testing'))
        if self.ctx.active_model is None:
            self.push_screen('model_search')
        else:
            self.push_screen('model_view')
    
    def on_model_change(self):
        # TODO: update context
        pass

if __name__ == '__main__':

    dbtui_front = dbtuiFrontend()
    dbtuiFrontend().run()
