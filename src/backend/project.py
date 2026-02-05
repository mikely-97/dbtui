import os 
from pathlib import Path
import yaml
from typing import Generator
from networkx import DiGraph
import logging


from ..common import DbtProjectAbstract, \
NonePathException, DbtModelNotFoundException, \
IncorrectFileExtensionException, NotWithinSubdirectoryException


from .model import DbtModel
from .property_claim import PropertyClaimAggregate
from .property_discovery import collect_model_claims


class DbtProject(DbtProjectAbstract):
    root_folder: Path 
    dbt_project_yml: Generator
    model_folder: str
    full_models_paths: list[Path]
    models: list[DbtModel]
    fall_back_to_filename: bool
    graph: DiGraph

    # optimizations for fetching models
    models_by_name: dict[str, DbtModel]
    models_by_file_name: dict[str, DbtModel]

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

    def collect_property_claims(self) -> None:
        """
        Collect all PropertyClaims for all models in the project.

        This method creates a PropertyClaimAggregate for each model and populates
        it with claims from all sources (dbt_project.yml, schema.yml, model SQL).
        The aggregates handle precedence resolution lazily when accessed.
        """
        for model in self.models:
            aggregate = PropertyClaimAggregate(model)
            claims = collect_model_claims(model)
            aggregate.add_all(claims)
            model.property_claims = aggregate
    
    def reset_models(self) -> None:
        self.models = []
        self.models_by_name = dict()
        self.models_by_file_name = dict()


    def load_models(self) -> None:
        self.reset_models()
        for models_path in self.full_models_paths:
            for root, _, files in models_path.walk():
                for file in files:
                    # Only load SQL files as models
                    if not file.endswith('.sql'):
                        continue
                    model = DbtModel(root / file, self)
                    self.models.append(model)
                    self.models_by_name[model.name] = model
                    self.models_by_file_name[model.file_name] = model


    def refresh(self):
        if not os.path.exists(self.root_folder):
            raise FileNotFoundError("Folder not found: %s" % self.root_folder)
        try:
            with open(self.root_folder / 'dbt_project.yml', 'r', encoding='utf-8') as f:
                self.parse_dbt_project(f.read())
            self.load_models()
            self.populate_graph()
            self.collect_property_claims()
        except FileNotFoundError:
            raise FileNotFoundError("dbt folder is present, but dbt_project.yml is not found: %s" % self.root_folder)


    def parse_dbt_project(self, dbt_project_raw: str) -> None:
        self.dbt_project_yml = yaml.load(dbt_project_raw, yaml.Loader)
        self.full_models_paths = [self.root_folder / folder for folder in self.dbt_project_yml['model-paths']]
        pass

    def get_model_by_name(self, name: str) -> DbtModel:
        model = self.models_by_name.get(name)
        if not model:
            raise DbtModelNotFoundException("dbt model not found: %s" % name)
        return model
    
    def get_model_by_file_name(self, file_name: str) -> DbtModel:
        model = self.models_by_file_name.get(file_name)
        if not model:
            raise DbtModelNotFoundException("dbt model not found: %s" % file_name)
        return model
    
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
        


