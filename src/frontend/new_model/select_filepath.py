from typing import TYPE_CHECKING
from textual.widgets import Input
from textual.validation import ValidationResult
if TYPE_CHECKING:
    from ..main import dbtuiFrontend


class SelectFilepath(Input):
    app: 'dbtuiFrontend'

    def on_input_submitted(self, event: Input.Submitted):
        if not event.validation_result.is_valid:
            # TODO: informative message (when the validators are in place)
            self.app.notify('Invalid path')
            return
        
        self.app.external_editor_command = event.value
