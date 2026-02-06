import subprocess
from abc import ABC, abstractmethod, ABCMeta
from typing import TYPE_CHECKING
from textual.screen import Screen
from .isolated import DbtModel, DbtProject

if TYPE_CHECKING:
    from ..main import DbtTuiFrontend

screen_metaclass = type(Screen)

class ScreenABCMeta(screen_metaclass, ABCMeta):
    pass


class DbtTuiScreen(Screen, ABC, metaclass=ScreenABCMeta):

    app: 'DbtTuiFrontend'

    @abstractmethod
    def on_model_change(self, model: DbtModel | None):
        NotImplemented

    @abstractmethod
    def on_project_change(self, project: DbtProject | None):
        NotImplemented

    def action_external_edit(self, model: DbtModel | None = None):
        """Open a model in an external editor.

        Args:
            model: The model to edit. If None, edits the currently selected model.
        """
        target_model = model or self.app.model
        if target_model is None:
            self.app.notify("No model selected.")
            return
        args = [self.app.external_editor_command, target_model.file_path_full.as_posix()]
        with self.app.suspend():
            try:
                subprocess.run(args=args, check=True)
            except FileNotFoundError:
                self.app.notify(f"Editor not found: {self.app.external_editor_command}")
            except subprocess.CalledProcessError as e:
                self.app.notify(f"Editor failed with exit code {e.returncode}")
            except Exception as e:
                raise e
        # Trigger reactive update if we edited the current model
        if target_model == self.app.model:
            self.app.model = self.app.model
