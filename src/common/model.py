from abc import ABC, abstractmethod
from typing import Iterable, Self

class DbtModelAbstract(ABC):

    @property
    @abstractmethod
    def parents(self) -> Iterable[Self]:
        NotImplemented

    @property
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

