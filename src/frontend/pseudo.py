import random 
import random
import uuid
from typing import Self

lorem = open('src/frontend/lorem.txt', 'r').read()

def rand_uuid() -> str:

    raw = uuid.uuid4()
    return raw.urn


class DbtModel:
    name: str 
    filepath: str
    text: str

    def __init__(self, name, filepath):
        self.name = name 
        self.filepath = filepath
        self.text = lorem
    
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

    
class DbtProject:
    name: str
    #models: list[DbtModel]

    def __init__(self, name):
        self.name = name

    def search_model(self, query) -> list[DbtModel]:
        result = []
        for _ in range(random.randint(2,5)):
            result.append(DbtModel.generate_random())
        return result
    
    def get_model_by_filepath(self, filepath: str) -> DbtModel:
        return DbtModel.generate_random()

    def get_model_by_name(self, name: str) -> DbtModel:
        return DbtModel.generate_random()


