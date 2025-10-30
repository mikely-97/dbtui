import os 
from os.path import join as opj
import yaml
from typing import Any, Generator
from jinja2 import Environment
from jinja2.nodes import Call, Const


class DbtModel:
    file_name: str
    file_path_full: str
    template: str

    def __init__(self, full_model_path: str):
        self.file_path_full = full_model_path
        self.file_name = os.path.basename(full_model_path)
        with open(full_model_path, 'r', encoding='utf-8') as f:
            self.template = f.read()

    
    @property 
    def name(self):
        # by default dbt sets model name as its filename without extension
        default_name = self.file_name.rpartition('.')[0]
        # we need to figure out if the model has been renamed with config() macro, so let's find this macro in the model file
        parsed_template = Environment().parse(self.template)
        calls = [i for i in parsed_template.find_all(Call) if i.node.name == 'config']

        # double config would be invalid
        # TODO: what do we do in case of double config?
        assert len(calls) < 2

        if not calls:
            return default_name
        else:
            config: Call = calls[0]
            kwargs = {item.key: item.value for item in config.kwargs}
            return kwargs.get('name', Const(default_name)).value
    pass


class DbtProject:
    root_folder: str 
    dbt_project_yml: Generator
    model_folder: str
    full_models_paths: list[str]
    models: list[DbtModel]

    def parse_dbt_project(self, dbt_project_raw: str) -> None:
        self.dbt_project_yml = yaml.load(dbt_project_raw, yaml.Loader)
        self.full_models_paths = [opj(self.root_folder, folder) for folder in self.dbt_project_yml['model-paths']]
        pass

    def load_models(self) -> None:
        for models_path in self.full_models_paths:
            for root, dirs, files in os.walk(models_path):
                for file in files:
                    self.models.append(DbtModel(opj(root, file)))

    def get_model_by_name(self, name: str) -> DbtModel:
        """
        I don't do dict interface, because I'm still not sure what I'm doing
        but gut feeling tells me I should use list as the basic structure
        sunce we can change names, directories, whatever, and this would require full update of dict each time
        then again, how large is a big dbt project? 100 models? 200?
        O(log(N)) vs O(N) wouldn't make that big of a difference here, but might introduce additional issues
        in any case, I will change this method if I change my mind
        """
        for model in self.models:
            if model.name == name:
                return model
        raise Exception("dbt model not found: %s" % name)
    
    def get_model_by_file_name(self, file_name: str) -> DbtModel:
        for model in self.models:
            if model.file_name == file_name:
                return model
        raise Exception("dbt model not found: %s" % file_name)

    def __init__(self, root_folder) -> None:
        self.models = []
        if not os.path.exists(root_folder):
            raise FileNotFoundError("Folder not found: %s" % root_folder)
        self.root_folder = root_folder
        try:
            with open(opj(self.root_folder, 'dbt_project.yml'), 'r', encoding='utf-8') as f:
                self.parse_dbt_project(f.read())
                self.load_models()
        except FileNotFoundError:
            raise FileNotFoundError("dbt folder is present, but dbt_project.yml is not found: %s" % root_folder)
        
        

