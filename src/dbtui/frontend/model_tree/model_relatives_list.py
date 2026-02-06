from typing import Literal
from ..common import ModelList, DbtModel
from .constants import PARENTS_ID, CHILDREN_ID

class ModelRelativesList(ModelList):

    id: Literal['parents', 'children']
    
    def on_model_change(self, model: DbtModel):
        if self.id == PARENTS_ID:
            self.populate_with_models(model.parents)
        elif self.id == CHILDREN_ID:
            self.populate_with_models(model.children)
        else:
            raise NotImplementedError
