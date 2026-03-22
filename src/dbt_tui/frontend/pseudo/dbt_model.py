import random
from typing import Self

from ...common import DbtModelAbstract
from .utils import lorem, rand_uuid


class DbtModel(DbtModelAbstract):
    """
    Pseudo model that imitates the interface of actual DbtModel class
    useful for testing and such, just to decouple stuff
    """
    name: str 
    file_path_relative: str
    text: str

    def __init__(self, name, filepath):
        self.name_raw = name 
        self.file_path_relative = filepath
    
    @classmethod
    def generate_random(cls):
        return cls(
            name=rand_uuid(),
            filepath= "/".join([
                rand_uuid(),
                rand_uuid()
            ])
        )
    @property
    def parents(self) -> list[Self]:
        result = []
        for _ in range(random.randint(2, 5)):
            result.append(self.generate_random())
        return result

    @property
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
