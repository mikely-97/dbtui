import subprocess
from abc import ABC, abstractmethod, ABCMeta
from typing import TYPE_CHECKING
from textual.screen import Screen
from .isolated import DbtModel, DbtProject

if TYPE_CHECKING:
    from ..main import dbtuiFrontend

screen_metaclass = type(Screen)

class ScreenABCMeta(screen_metaclass, ABCMeta):
    pass


class DbtuiScreen(Screen, ABC, metaclass=ScreenABCMeta):

    app: 'dbtuiFrontend'

    @abstractmethod
    def on_model_change(self, model: DbtModel):
        NotImplemented

    # @abstractmethod
    def on_project_change(self, project: DbtProject):
        NotImplemented

    def action_external_edit(self):
        # TODO: external edit for an arbitrary model
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
