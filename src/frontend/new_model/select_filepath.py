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
        elif Path(value).exists():
            return self.failure("The path already exists")
        elif Path(value).suffix and Path(value).suffix != '.sql':
            return self.failure("The file extension should be .sql or none")
            
        return self.success()


class SelectFilepath(Input):
    app: 'dbtuiFrontend'
    validators = [IsRelPathString]

    def on_input_submitted(self, event: Input.Submitted):
        if not event.validation_result.is_valid:
            self.app.notify(event.validation_result.failure_descriptions[0])
            return
        
        # making sure there's the .sql file extension 
        if not Path(event.value).suffix:
            value = Path('.'.join([event.value, 'sql']))
        else:
            value = Path(event.value)
        
        try:
            self.app.model = self.app.project.create_new_model(value, self.app.model)
        except Exception as e:
            self.app.notify(e.args[0])
