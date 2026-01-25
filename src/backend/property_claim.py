from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Self
from .model import DbtModel

@dataclass
class PropertyClaim:
    source_type: Literal["dbt_project.yml", "schema.yml", "model"]
    source_path: Path
    model: DbtModel
    name: str
    value: Any
    kind: Literal["config", "property"]
    yaml_path: str|None=None # for dbt_project.yml
    effective: bool=True # for dbt_project.yml: we need to make sure that the property corresponds to the path

    def __gt__(self, other: Self) -> bool:
        # exception means they are equal
        if self.model != other.model:
            raise Exception('Models are different!')
        if self.name != other.name:
            raise Exception('Properties are different!')
        
        if self.source_type == 'model':
            if other.source_type == 'model':
                raise Exception('Two identical fields in the same model config!')
            else:
                return True
        
        elif self.source_type == 'schema.yml':
            if other.source_type == 'schema.yml':
                if self.source_path.resolve() == other.source_path.resolve():
                    raise Exception('Two identical fields for the same model in the same yml config!')
                else: 
                    raise Exception('Resources can be defined in schema.yml only once!')
            else:
                return other.source_type == 'dbt_project.yml'
        
        elif self.source_type == 'dbt_project.yml':
            if self.yaml_path == other.yaml_path:
                raise Exception('Double config in dbt_project.yml!')
            # if both aren't effective, we don't care - might as well calculate, but they would both be greyed out
            elif self.effective and not other.effective: 
                return True 
            else: 
                return len(self.yaml_path) > len(other.yaml_path)

        
            


