from pathlib import Path
from typing import TYPE_CHECKING

from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.validation import ValidationResult, Validator

from ..common import DbtModel, DbtProject
from .select_filepath import SelectFilepath

if TYPE_CHECKING:
    from ..main import DbtTuiFrontend



class IsRelPathString(Validator):
    def validate(self, value: str) -> ValidationResult:
        if Path(value).is_absolute():
            return self.failure('The path must be relative to the project root')
        elif Path(value).exists():
            return self.failure("The path already exists")
        elif Path(value).suffix and Path(value).suffix != '.sql':
            return self.failure("The file extension should be .sql or none")
            
        return self.success()

class NewModel(ModalScreen):

    app: 'DbtTuiFrontend'


    def compose(self):
       yield SelectFilepath(
           placeholder='enter the file path',
           suggester=SuggestFromList(suggestions=[path.as_posix() for path in self.app.project.full_models_paths]),
           validators = [IsRelPathString()],
           validate_on=['changed', 'submitted'],
       ) 
    
    def on_model_change(self, model: DbtModel|None):
        # it's supposed to be due to a successful model creation
        self.dismiss()
    
    def on_project_change(self, project: DbtProject|None):
        # we don't care here
        pass
