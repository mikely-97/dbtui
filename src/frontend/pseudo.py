import random
import uuid
from typing import Self
from pathlib import Path
from ..common import DbtModelAbstract, DbtProjectAbstract, NonePathException

lorem = open('src/frontend/lorem.txt', 'r').read()

def rand_uuid() -> str:

    raw = uuid.uuid4()
    return raw.urn


class DbtModel(DbtModelAbstract):
    """
    Pseudo model that imitates the interface of actual DbtModel class
    useful for testing and such, just to decouple stuff
    """
    name: str 
    filepath: str
    text: str

    def __init__(self, name, filepath):
        self.name_raw = name 
        self.filepath = filepath
    
    @classmethod
    def generate_random(cls):
        return cls(
            name=rand_uuid(),
            filepath= "/".join([
                rand_uuid(),
                rand_uuid()
            ])
        )

    def parents(self) -> list[Self]:
        result = []
        for _ in range(random.randint(2, 5)):
            result.append(self.generate_random())
        return result

    def children(self) -> list[Self]:
        result = []
        for _ in range(random.randint(2, 5)):
            result.append(self.generate_random())
        return result

    @property
    def name(self) -> str:
        return self.name_raw
    
    @property
    def text(self) -> str:
        return lorem


    
class DbtProject(DbtProjectAbstract):
    name: str
    root_folder: str
    
    #models: list[DbtModel]

    def __init__(self, project_path: Path|str):
        self.name = 'name placeholder'
        if project_path is None:
            raise NonePathException
        else:
            self.root_folder = Path(project_path)

    def search_model(self, query) -> list[DbtModel]:
        result = []
        for _ in range(random.randint(2,5)):
            result.append(DbtModel.generate_random())
        return result
    
    def get_model_by_file_name(self, file_name: str) -> DbtModel:
        return DbtModel.generate_random()

    def get_model_by_name(self, name: str) -> DbtModel:
        return DbtModel.generate_random()


