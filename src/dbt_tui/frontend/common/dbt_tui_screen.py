import subprocess
from abc import ABC, ABCMeta
from typing import TYPE_CHECKING

from textual.screen import Screen

from .isolated import DbtModel, DbtProject
from .messages import ModelFileChanged

if TYPE_CHECKING:
    from ..main import DbtTuiFrontend

screen_metaclass = type(Screen)


class ScreenABCMeta(screen_metaclass, ABCMeta):
    pass


class DbtTuiScreen(Screen, ABC, metaclass=ScreenABCMeta):
    """
    Base class for all dbt-tui screens.

    Screens can react to state changes by implementing handlers:
    - on_model_change(self, model) -> None
    - on_project_change(self, project) -> None

    These methods have default no-op implementations, so screens only need
    to override the ones they care about.
    """

    app: 'DbtTuiFrontend'

    def on_model_change(self, model: DbtModel | None) -> None:
        """
        Called when the active model changes.

        Override this method to react to model changes.
        Default implementation does nothing.
        """
        pass

    def on_project_change(self, project: DbtProject | None) -> None:
        """
        Called when the active project changes.

        Override this method to react to project changes.
        Default implementation does nothing.
        """
        pass

    def action_external_edit(self, model: DbtModel | None = None) -> None:
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
        # Invalidate the model's text cache after external edit
        if target_model is not None:
            target_model.invalidate_cache()
        # Post a message to notify other components
        self.post_message(ModelFileChanged(target_model))
        # Trigger reactive update if we edited the current model
        if target_model == self.app.model:
            self.app.model = self.app.model
