import random

from pathlib import Path

from ...common import DbtProjectAbstract, DbtModelAbstract, NonePathException
from .dbt_model import DbtModel

class DbtProject(DbtProjectAbstract):
    name: str
    root_folder: Path
    
    models: list[DbtModel]

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
    
    def get_model_folders(self) -> list[Path]:
        return [self.root_folder/'models']
    
    def create_new_model(self, filepath: Path, from_: DbtModelAbstract | None = None) -> DbtModel:
        return DbtModel.generate_random()
