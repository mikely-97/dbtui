
from abc import ABC, abstractmethod
from typing import Iterable
from .model import DbtModelAbstract
from pathlib import Path

class DbtProjectAbstract(ABC):

    @abstractmethod
    def search_model(self, query) -> Iterable[DbtModelAbstract]:
        NotImplemented
    
    @abstractmethod
    def get_model_by_file_name(self, file_name: str) -> DbtModelAbstract:
        NotImplemented

    @abstractmethod
    def get_model_by_name(self, name: str) -> DbtModelAbstract:
        NotImplemented
    
    @abstractmethod
    def __init__(self, project_path: Path|str):
        NotImplemented
    
    @abstractmethod
    def get_model_folders(self) -> list[Path]:
        NotImplemented
    
    @abstractmethod
    def create_new_model(self, filepath: Path, from_: DbtModelAbstract|None=None) -> DbtModelAbstract:
        NotImplemented

