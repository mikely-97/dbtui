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
from .property_viewer.property_viewer import PropertyViewerScreen
from .lineage_view.lineage_view import ColumnLineageView
from .help_screen.help_screen import HelpScreen

from ..common import DbtTuiCache, load_cache, save_cache, NonePathException
from ..common.cache import WorkspaceEntry
from ..common.logging import get_logger
from .common import DbtTuiScreen, DbtProject, DbtModel
from .common.timing import TimingContext
from .common.project_tab_bar import ProjectTabBar

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
        Binding("v", "push_screen('property_viewer')", "properties"),
        Binding("d", "push_screen('dag_view')", "DAG"),
        Binding("l", "push_screen('lineage_view')", "Lineage"),
        Binding("?", "push_screen('help')", "help"),
    ]

    SCREENS = {
        'model_search': ModelSearch,
        'model_view': ModelTree,
        'model_properties': ModelView,
        'options': Options,
        'project_search': ProjectSearch,
        'new_model': NewModel,
        'dag_view': DagView,
        'property_viewer': PropertyViewerScreen,
        'lineage_view': ColumnLineageView,
        'help': HelpScreen,
        }

    screen_stack: list[DbtTuiScreen]
    external_editor_command: reactive[str] = reactive('vi')

    projects: list = []
    active_project_index: int = 0

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
        

    def add_project(self, project) -> None:
        """Add a project to the workspace and switch to it."""
        self.projects = [*self.projects, project]
        self.active_project_index = len(self.projects) - 1
        self.project = project
        self.model = None
        self._refresh_tab_bar()

    def switch_project(self, index: int) -> None:
        """Switch to a project by index."""
        if 0 <= index < len(self.projects):
            self.active_project_index = index
            self.project = self.projects[index]
            self.model = None
            self._refresh_tab_bar()

    def _refresh_tab_bar(self) -> None:
        try:
            tab_bar = self.query_one('#project-tab-bar', ProjectTabBar)
            tab_bar.refresh_projects(self.projects, self.active_project_index)
        except Exception:
            pass

    def on_project_tab_bar_project_selected(self, event) -> None:
        idx = event.index
        if 0 <= idx < len(self.projects):
            self.active_project_index = idx
            self.project = self.projects[idx]
            self.model = None
            self._refresh_tab_bar()

    def on_project_tab_bar_add_project_requested(self, event) -> None:
        self.push_screen('project_search')

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
        save_cache(DbtTuiCache(
            last_open_project_raw=str(self.project.root_folder) if isinstance(self.project, DbtProject) else None,
            last_active_model=self.model.name if isinstance(self.model, DbtModel) else None,
            external_editor_command=self.external_editor_command,
            workspaces=[
                WorkspaceEntry(
                    project_path=str(p.root_folder),
                    last_model=self.model.name if self.model and p is self.project else None,
                )
                for p in self.projects
            ],
        ))

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
    

    async def on_mount(self):
        logger.debug("App mounting, loading context")
        cache: DbtTuiCache = load_cache()
        self.load_context()

        # Mount tab bar
        tab_bar = ProjectTabBar(id='project-tab-bar')
        await self.mount(tab_bar)

        # Restore workspaces from cache (additional projects beyond the primary)
        primary_path = str(self.project.root_folder) if self.project else ''
        for ws in cache.workspaces:
            if ws.project_path != primary_path:
                try:
                    extra = DbtProject(ws.project_path)
                    self.projects = [*self.projects, extra]
                except Exception as e:
                    logger.warning(f"Failed to restore workspace {ws.project_path}: {e}")

        # Ensure primary project is in the list
        if self.project and self.project not in self.projects:
            self.projects = [self.project, *self.projects]
            self.active_project_index = 0

        self._refresh_tab_bar()

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
