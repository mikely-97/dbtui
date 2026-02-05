
from src.common.model import DbtModelAbstract
from pathlib import Path
from jinja2 import Environment, Template
from jinja2.nodes import Call, Const
import logging

from ..common import DbtModelAbstract, NotWithinSubdirectoryException

from typing import TYPE_CHECKING, Iterable, Self
if TYPE_CHECKING:
    from .project import DbtProject
    from .property_claim import PropertyClaimAggregate


class DbtModel(DbtModelAbstract):
    file_name: str
    file_path_full: Path
    file_path_relative: Path
    template: str
    parsed_template: Template
    project: 'DbtProject'
    property_claims: 'PropertyClaimAggregate | None'

    @property 
    def file_path_relative(self):
        return self.file_path_full.relative_to(self.project.root_folder)
    
    @property
    def file_name(self):
        return self.file_path_full.name

    def __init__(self, file_path_full: Path, project: 'DbtProject'):
        self.file_path_full = file_path_full
        self.project = project
        self.property_claims = None  # Populated by DbtProject.collect_property_claims()
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

