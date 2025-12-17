from typing import TYPE_CHECKING
from textual.widgets import Input
from pathlib import Path
from textual.validation import ValidationResult, Validator
if TYPE_CHECKING:
    from ..main import dbtuiFrontend

class IsRelPathString(Validator):
    def validate(self, value: str) -> ValidationResult:
        if Path(value).is_absolute():
            return self.failure('The path must be relative to the project root')
        
        return self.success()


class SelectFilepath(Input):
    app: 'dbtuiFrontend'

    def on_input_submitted(self, event: Input.Submitted):
        if not event.validation_result.is_valid:
            # TODO: informative message (when the validators are in place)
            self.app.notify('Invalid path')
            return
        
        self.app.external_editor_command = event.value
