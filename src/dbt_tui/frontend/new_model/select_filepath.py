from typing import TYPE_CHECKING
from textual.widgets import Input
from pathlib import Path
if TYPE_CHECKING:
    from ..main import DbtTuiFrontend


class SelectFilepath(Input):
    app: 'DbtTuiFrontend'

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

    def on_input_changed(self, event: Input.Submitted):
        if not event.validation_result.is_valid:
            self.app.notify(event.validation_result.failure_descriptions[0])
            return
