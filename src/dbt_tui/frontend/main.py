from dataclasses import dataclass

from textual.app import App 
from textual.binding import Binding
from textual.reactive import reactive
from typing import Any 

from .model_search.model_search import ModelSearch
from .model_tree.model_tree import ModelTree
from .model_view import ModelView
from .options.options import Options
from .project_search.project_search import ProjectSearch
from .new_model import NewModel
from .dag_view.dag_view import DagView

from ..common import DbtTuiCache, load_cache, save_cache, NonePathException
from ..common.logging import get_logger
from .common import DbtTuiScreen, DbtProject, DbtModel
from .common.timing import TimingContext

logger = get_logger('frontend.main')

@dataclass
class AppContext:
    project: DbtProject|None = None
    model: DbtModel|None = None



class DbtTuiFrontend(App):

    BINDINGS = [
        Binding("q", "quit", "quit"),
        Binding("o", "push_screen('options')", "options"),
        Binding("f", "push_screen('model_search')", "find model"),
        Binding("p", "push_screen('project_search')", "project"),
        Binding("v", "push_screen('model_properties')", "properties"),
        Binding("d", "push_screen('dag_view')", "DAG"),
    ]

    SCREENS = {
        'model_search': ModelSearch,
        'model_view': ModelTree,
        'model_properties': ModelView,
        'options': Options,
        'project_search': ProjectSearch,
        'new_model': NewModel,
        'dag_view': DagView,
        }

    screen_stack: list[DbtTuiScreen]
    external_editor_command: reactive[str] = reactive('vi')

    # For debounced save
    _save_timer = None
    _SAVE_DEBOUNCE_SECONDS = 0.5  # Save at most every 500ms

    def watch_external_editor_command(self, old_value: str, new_value: str):
        self.save_context_debounced()

    project: reactive[DbtProject|None] = reactive(None, always_update=True, init=True)

    def validate_project(self, project: Any) -> DbtProject|None:
        if not isinstance(project, DbtProject):
            return None
        return project

    def on_project_change(self, project: DbtProject|None):
        self.save_context_debounced()
        for screen in self.screen_stack:
            if not screen.id == '_default':
                screen.on_project_change(project)
    
    def watch_project(self, old_project: DbtProject|None, new_project: DbtProject|None):
        self.on_project_change(new_project)

    model: reactive[DbtModel|None] = reactive(None, always_update=True, init=True)


    def validate_model(self, model: Any) -> DbtModel|None:
        if not isinstance(model, DbtModel):
            return None 
        return model
    
    def on_model_change(self, model: DbtModel|None):
        timing = TimingContext("on_model_change")

        with timing.step("save_context_debounced"):
            self.save_context_debounced()

        for screen in self.screen_stack:
            if not screen.id == '_default':
                with timing.step(f"screen.{screen.__class__.__name__}.on_model_change"):
                    screen.on_model_change(model)

        with timing.step("push_screen"):
            self.push_screen('model_view')

        timing.log()
    
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
        cache: DbtTuiCache = load_cache(clear_cache)
        project = None
        model = None
        try:
            project = DbtProject(project_path=cache.last_open_project)
        except NonePathException:
            pass # that means we don't have anything saved, so don't log anything
        except Exception as e:
            logger.warning(f"Failed to load project {cache.last_open_project} for reason: {e.args}")
        if project is not None:
            try:
                model = project.get_model_by_name(cache.last_active_model)
            except Exception as e:
                logger.warning(f"Failed to load model: {e.args}")
        self.project = project 
        self.model = model
        self.external_editor_command = cache.external_editor_command
        
    def save_context(self):
        """Save context immediately (blocking)."""
        save_cache(
            project_path=self.project.root_folder if isinstance(self.project, DbtProject) else None,
            model_name=self.model.name if isinstance(self.model, DbtModel) else None,
            external_editor_command=self.external_editor_command,
        )

    def save_context_debounced(self):
        """Schedule a debounced save - coalesces rapid changes into one save."""
        if self._save_timer is not None:
            self._save_timer.stop()
        self._save_timer = self.set_timer(
            self._SAVE_DEBOUNCE_SECONDS,
            self._do_debounced_save
        )

    def _do_debounced_save(self):
        """Callback for debounced save timer."""
        self._save_timer = None
        self.save_context()
    

    def on_mount(self):
        logger.debug("App mounting, loading context")
        self.load_context()
        if self.project is None:
            logger.debug("No project loaded, showing project search")
            self.push_screen('project_search')
        elif self.model is None:
            logger.debug(f"Project loaded ({self.project.root_folder.name}), showing model search")
            self.push_screen('model_search')
        else:
            logger.info(f"Loaded project '{self.project.root_folder.name}' with model '{self.model.name}'")
            self.push_screen('model_view')

if __name__ == '__main__':

    dbt_tui_front = DbtTuiFrontend()
    DbtTuiFrontend().run()
