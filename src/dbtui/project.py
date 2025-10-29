import os 
from os.path import join as opj
import yaml
from typing import Any, Generator


class DbtModel:
    pass


class DbtProject:
    root_folder: str 
    dbt_project_yml: Generator
    model_folder: str
    models: list[DbtModel]

    def parse_dbt_project(self, dbt_project_raw: str) -> None:
        self.dbt_project_yml = yaml.load(dbt_project_raw, yaml.Loader)
        self.full_models_paths = [opj(self.root_folder, folder) for folder in self.dbt_project_yml['model-paths']]
        print(self.dbt_project_yml)
        print(self.full_models_paths)
        pass

    def __init__(self, root_folder) -> None:
        if not os.path.exists(root_folder):
            raise FileNotFoundError("Folder not found: %s" % root_folder)
        self.root_folder = root_folder
        try:
            with open(opj(self.root_folder, 'dbt_project.yml'), 'r', encoding='utf-8') as f:
                self.parse_dbt_project(f.read())
        except FileNotFoundError:
            raise FileNotFoundError("dbt folder is present, but dbt_project.yml is not found: %s" % root_folder)
        
        

