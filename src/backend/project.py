import os 
from pathlib import Path
import yaml
from typing import Generator, Iterable, Self
from jinja2 import Environment, Template
from jinja2.nodes import Call, Const
from networkx import DiGraph
import logging

from src.common.model import DbtModelAbstract

from ..common import DbtModelAbstract, DbtProjectAbstract, \
NonePathException, DbtModelNotFoundException, \
IncorrectFileExtensionException, NotWithinSubdirectoryException




class DbtModel(DbtModelAbstract):
    file_name: str
    file_path_full: Path
    file_path_relative: Path
    template: str
    parsed_template: Template
    project: 'DbtProject'

    @property 
    def file_path_relative(self):
        return self.file_path_full.relative_to(self.project.root_folder)
    
    @property
    def file_name(self):
        return self.file_path_full.name

    def __init__(self, file_path_full: Path, project: 'DbtProject'):
        self.file_path_full = file_path_full
        self.project = project
        with open(file_path_full, 'r', encoding='utf-8') as f:
            self.template = f.read()
        self.parsed_template = Environment().parse(self.template)

    def _find_calls(self, macro_name: str):
        return [i for i in self.parsed_template.find_all(Call) if i.node.name == macro_name]

    
    @property 
    def name(self) -> str:
        # by default dbt sets model name as its filename without extension
        default_name = self.file_name.rpartition('.')[0]
        # we need to figure out if the model has been renamed with config() macro, so let's find this macro in the model file
        calls = self._find_calls('config')

        # double config would be invalid
        if len(calls) > 1:
            logging.warn("Duplicated invocation of config() in %s" % self.file_path_relative)
            return default_name

        if not calls:
            return default_name
        else:
            config: Call = calls[0]
            kwargs = {item.key: item.value for item in config.kwargs}
            return kwargs.get('name', Const(default_name)).value
    
    @property 
    def children(self) -> list[Self]:
        return sorted(list(self.project.graph.successors(self)), key=lambda n: n.name)
    
    @property 
    def parents(self) -> Iterable[Self]:
        return sorted(list(self.project.graph.predecessors(self)), key=lambda n: n.name)
    
    @property
    def text(self) -> str:
        with open(self.file_path_full, 'r', encoding='utf-8') as f:
            self.template = f.read()
        return self.template
    
    
    @property
    def refs(self) -> list[str]:
        result = []
        for call in self._find_calls('ref'):
            if len(call.args) != 1:
                logging.warn(f"Invalid number of args to ref() in model {self.name}: should be one, but it's {len(call.args)}: {[arg.value for arg in call.args]}")
                continue
            result.append(call.args[0].value)
        return result
    


class DbtProject(DbtProjectAbstract):
    root_folder: Path 
    dbt_project_yml: Generator
    model_folder: str
    full_models_paths: list[Path]
    models: list[DbtModel]
    fall_back_to_filename: bool
    graph: DiGraph

    def populate_graph(self):
        self.graph = DiGraph()
        for model in self.models:
            self.graph.add_node(model)
            for ref in model.refs:
                referenced_model = None
                try:
                    referenced_model = self.get_model_by_name(ref)
                except DbtModelNotFoundException:
                    if self.fall_back_to_filename:
                        try:
                            referenced_model = self.get_model_by_file_name(ref+'.sql')
                        except DbtModelNotFoundException:
                            logging.warn(f"{model.name} references {ref} which is not found as a name or a filename")
                    else:
                        logging.warn(f"{model.name} references {ref} which is not found as a name")
                finally:
                    if referenced_model:
                        self.graph.add_node(referenced_model)
                        self.graph.add_edge(referenced_model, model)
                        
        pass

    def refresh(self):
        if not os.path.exists(self.root_folder):
            raise FileNotFoundError("Folder not found: %s" % self.root_folder)
        self.models = []
        try:
            with open(self.root_folder / 'dbt_project.yml', 'r', encoding='utf-8') as f:
                self.parse_dbt_project(f.read())
                self.load_models()
                self.populate_graph()
        except FileNotFoundError:
            raise FileNotFoundError("dbt folder is present, but dbt_project.yml is not found: %s" % self.root_folder)


    def parse_dbt_project(self, dbt_project_raw: str) -> None:
        self.dbt_project_yml = yaml.load(dbt_project_raw, yaml.Loader)
        self.full_models_paths = [self.root_folder / folder for folder in self.dbt_project_yml['model-paths']]
        pass

    def load_models(self) -> None:
        for models_path in self.full_models_paths:
            for root, _, files in models_path.walk():
                for file in files:
                    self.models.append(DbtModel(root / file, self))

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
        raise DbtModelNotFoundException("dbt model not found: %s" % name)
    
    def get_model_by_file_name(self, file_name: str) -> DbtModel:
        for model in self.models:
            if model.file_name == file_name:
                return model
        raise DbtModelNotFoundException("dbt model not found: %s" % file_name)
    
    def search_model(self, query) -> list[DbtModel]:
        try:
            return [self.get_model_by_name(query)]
        except DbtModelNotFoundException:
            # TODO: get inspiration from dbt own selector resolver
            return []
        

    def __init__(self, project_path: Path|str, fall_back_to_filename: bool = False) -> None:
        if project_path is None:
            raise NonePathException("project_path is None")
        if isinstance(project_path, str):
            project_path = Path(project_path) # TODO: raise some fancy error if not convertible
        self.fall_back_to_filename = fall_back_to_filename
        self.root_folder = project_path
        self.refresh()

        
    def graph_repr(self):
        return '\n'.join(sorted([f"({parent.name}) --> ({child.name})" for parent, child in self.graph.edges]))
            
    
    def get_model_folders(self) -> list[Path]:
        """
        Notice: this returns all folders in which models are,
        not the model folder ROOTS that are defined in dbt_project.yml!
        We need this method to suggest where to save a new model!
        """
        result_set: set[Path] = set()
        for model in self.models:
            result_set.add(model.file_path_relative.parent)
        return sorted(list(result_set))

    def create_new_model(self, filepath: Path, from_: DbtModel | None=None) -> DbtModel:
        # TODO: cover with tests (when u're sure it works as u imagined)
        if filepath.is_dir():
            raise IsADirectoryError(f"This filepath is an existing folder: {filepath.as_posix()}")
        elif filepath.exists():
            raise FileExistsError(f"Another file exists at this path: {filepath.as_posix()}")
        elif filepath.suffix != '.sql':
            raise IncorrectFileExtensionException(f"dbt models should be <.sql> files, but <{filepath.suffix}> given")
        elif filepath.is_absolute():
            # will raise an exception with required details if not a subfolder
            filepath.relative_to(self.root_folder)

        if isinstance(from_, DbtModel):
            text = "SELECT * FROM {{ ref('%s') }}" % from_.name
        else: 
            text = ''
        
        filepath_prepared = filepath if filepath.is_absolute() else self.root_folder / filepath

        check_if_in_model_paths = 0
        for model_path in self.full_models_paths:
            try:
                check_if_in_model_paths += bool(filepath_prepared.relative_to(model_path))
            except ValueError:
                pass 
        if not check_if_in_model_paths:
            raise ValueError('The filepath is not in model folders as defined by dbt_project.yml')
  

        filepath_prepared.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath_prepared, mode='w', encoding='utf-8') as f:
            f.write(text)
        
        self.refresh()

        return self.get_model_by_name(filepath_prepared.stem)
        


