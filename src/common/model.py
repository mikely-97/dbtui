from abc import ABC, abstractmethod
from typing import Iterable, Self

class DbtModelAbstract(ABC):

    @abstractmethod
    def parents(self) -> Iterable[Self]:
        NotImplemented

    @abstractmethod
    def children(self) -> Iterable[Self]:
        NotImplemented

    @property
    @abstractmethod
    def name(self) -> str:
        NotImplemented
    
    @property
    @abstractmethod
    def text(self) -> str:
        NotImplemented

