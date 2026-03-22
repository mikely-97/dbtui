from typing import Literal

from ...common.entity import EntityType
from ..common import DbtModel, ModelList
from .constants import CHILDREN_ID, PARENTS_ID


class ModelRelativesList(ModelList):

    id: Literal['parents', 'children']

    def _allowed_types(self) -> set[EntityType] | None:
        from .model_tree import ModelTree
        if isinstance(self.screen, ModelTree):
            return self.screen.allowed_entity_types
        return None

    def on_model_change(self, model: DbtModel):
        if self.id == PARENTS_ID:
            entities = list(model.parents)
        elif self.id == CHILDREN_ID:
            entities = list(model.children)
        else:
            raise NotImplementedError

        allowed = self._allowed_types()
        if allowed is not None:
            entities = [e for e in entities if e.entity_type in allowed]

        self.populate_with_entities(entities)
