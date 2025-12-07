from os.path import exists
import subprocess
from abc import ABC, abstractmethod, ABCMeta
from typing import Iterable, TYPE_CHECKING

from textual import widgets, containers, screen
from textual.binding import Binding

if TYPE_CHECKING:
    from .main import dbtuiFrontend

isolated = exists('.isolated')
if isolated:
    from .pseudo import DbtModel, DbtProject
else:
    from ..backend.project import DbtModel, DbtProject

screen_metaclass = type(screen.Screen)

class ScreenABCMeta(screen_metaclass, ABCMeta):
    pass

class DbtuiScreen(screen.Screen, ABC, metaclass=ScreenABCMeta):

    app: 'dbtuiFrontend'

    @abstractmethod
    def on_model_change(self, model: DbtModel):
        NotImplemented

    # @abstractmethod
    def on_project_change(self, project: DbtProject):
        NotImplemented

    def action_external_edit(self):
        if self.app.model is None:
            self.app.notify("No model selected.")
            return  
        args = [self.app.external_editor_command, self.app.model.file_path_full.as_posix()]
        with self.app.suspend():
            try:
                subprocess.run(args=args, check=True)
            except FileNotFoundError:
                self.app.notify(f"Editor not found: {self.app.external_editor_command}")
            except subprocess.CalledProcessError as e:
                self.app.notify(f"Editor failed with exit code {e.returncode}")
            except Exception as e:
                raise e 
        # it will trigger reactive update bc changing a reactive's attribute doesn't trigger it
        self.app.model = self.app.model



class ModelListItem(widgets.ListItem):

    dbt_model: DbtModel

    def __init__(self, model: DbtModel, **kwargs):

        super().__init__(
            containers.VerticalGroup(
                widgets.Label(model.name),
                widgets.Rule(),
                widgets.Label(str(model.file_path_relative)),
            ),
            **kwargs
        )
        self.dbt_model = model
    


    

class ModelList(widgets.ListView):

    BINDINGS =  [
        Binding("j", "cursor_down()", show=False),
        Binding("k", "cursor_up()", show=True,),
    ]

    app: 'dbtuiFrontend'

    def populate_with_models(self, models: Iterable[DbtModel]):
        self.clear()
        for model in models:
            self.append(
                ModelListItem(
                    model=model
                )
            )
        # we want to instantly focus on the first index
        self.index = None
        self.action_cursor_down()
        # TODO: when tampering with CSS, check out how u can fix the invisible highlight
        
        
    def change_model(self, model: DbtModel):
        # triggers the reactive component
        self.app.model = model

        
    
    def on_list_view_selected(self, event: widgets.ListView.Selected) -> None: 
        list_item: ModelListItem = event.item 
        dbt_model = list_item.dbt_model
        assert isinstance(dbt_model, DbtModel)
        self.change_model(dbt_model)


        



