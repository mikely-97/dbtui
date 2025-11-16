
from abc import ABC, abstractmethod
from typing import Iterable
from .model import DbtModelAbstract

class DbtProjectAbstract(ABC):

    @abstractmethod
    def search_model(self, query) -> Iterable[DbtModelAbstract]:
        NotImplemented
    
    @abstractmethod
    def get_model_by_file_name(self, file_name: str) -> DbtModelAbstract:
        NotImplemented

    def get_model_by_name(self, name: str) -> DbtModelAbstract:
        NotImplemented

