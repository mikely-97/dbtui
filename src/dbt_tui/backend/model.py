from pathlib import Path
from jinja2 import Environment, Template
from jinja2.nodes import Call, Const

from ..common import DbtModelAbstract, NotWithinSubdirectoryException
from ..common.entity import DbtEntityAbstract, EntityType
from ..common.logging import get_logger

from typing import TYPE_CHECKING, Iterable
if TYPE_CHECKING:
    from .project import DbtProject
    from .property_claim import PropertyClaimAggregate


logger = get_logger('backend.model')


class DbtModel(DbtModelAbstract):
    _file_path_full: Path
    _template: str
    _template_mtime: float  # Track file modification time for cache invalidation
    parsed_template: Template
    project: 'DbtProject'
    property_claims: 'PropertyClaimAggregate | None'

    @property
    def file_path_full(self) -> Path:
        return self._file_path_full

    @property
    def file_path_relative(self) -> Path:
        return self._file_path_full.relative_to(self.project.root_folder)

    @property
    def file_name(self) -> str:
        return self._file_path_full.name

    @property
    def entity_type(self) -> EntityType:
        return "model"

    def __init__(self, file_path_full: Path, project: 'DbtProject'):
        self._file_path_full = file_path_full
        self.project = project
        self.property_claims = None  # Populated by DbtProject.collect_property_claims()
        self._template_mtime = file_path_full.stat().st_mtime
        with open(file_path_full, 'r', encoding='utf-8') as f:
            self._template = f.read()
        self.parsed_template = Environment().parse(self._template)

    def invalidate_cache(self) -> None:
        """Force re-read of file contents on next access."""
        self._template_mtime = 0

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
            logger.warning("Duplicated invocation of config() in %s" % self.file_path_relative)
            return default_name

        if not calls:
            return default_name
        else:
            config: Call = calls[0]
            kwargs = {item.key: item.value for item in config.kwargs}
            return kwargs.get('name', Const(default_name)).value

    @property
    def tags(self) -> list[str]:
        """Return tags from config(tags=[...]) or config(tags='single')."""
        calls = self._find_calls('config')
        if not calls:
            return []
        config: Call = calls[0]
        kwargs = {item.key: item.value for item in config.kwargs}
        tag_node = kwargs.get('tags')
        if tag_node is None:
            return []
        from jinja2.nodes import List as JinjaList, Const as JinjaConst
        if isinstance(tag_node, JinjaList):
            return [item.value for item in tag_node.items if isinstance(item, JinjaConst)]
        if isinstance(tag_node, JinjaConst):
            return [tag_node.value]
        return []

    @property
    def materialized(self) -> str:
        """Return materialization from config(materialized=...), default 'view'."""
        calls = self._find_calls('config')
        if not calls:
            return 'view'
        config: Call = calls[0]
        kwargs = {item.key: item.value for item in config.kwargs}
        mat_node = kwargs.get('materialized')
        if mat_node is None:
            return 'view'
        return str(mat_node.value)

    @property
    def children(self) -> list[DbtEntityAbstract]:
        return sorted(list(self.project.graph.successors(self)), key=lambda n: n.name)

    @property
    def parents(self) -> Iterable[DbtEntityAbstract]:
        return sorted(list(self.project.graph.predecessors(self)), key=lambda n: n.name)

    @property
    def macro_calls(self) -> list[str]:
        """Return macro names called in this model (excluding dbt/Jinja builtins)."""
        BUILTIN_MACROS = {
            'ref', 'source', 'config', 'log', 'var', 'env_var', 'run_query',
            'execute', 'this', 'adapter', 'modules', 'flags', 'graph',
            'model', 'return', 'exceptions', 'fromjson', 'tojson',
            'fromyaml', 'toyaml', 'zip', 'zip_strict', 'print', 'set',
            'load_result', 'store_result', 'submit_python_job',
        }
        result = []
        for call in self.parsed_template.find_all(Call):
            if hasattr(call.node, 'name') and call.node.name not in BUILTIN_MACROS:
                result.append(call.node.name)
        return result
    
    @property
    def text(self) -> str:
        """
        Return the model's SQL text content.

        Uses cached content unless file has been modified since last read.
        """
        try:
            current_mtime = self._file_path_full.stat().st_mtime
            if current_mtime > self._template_mtime:
                # File has changed, reload
                with open(self._file_path_full, 'r', encoding='utf-8') as f:
                    self._template = f.read()
                self._template_mtime = current_mtime
                self.parsed_template = Environment().parse(self._template)
        except OSError:
            # File might be deleted or inaccessible, return cached content
            pass
        return self._template
    
    
    @property
    def refs(self) -> list[str]:
        result = []
        for call in self._find_calls('ref'):
            if len(call.args) != 1:
                logger.warning(f"Invalid number of args to ref() in model {self.name}: should be one, but it's {len(call.args)}: {[arg.value for arg in call.args]}")
                continue
            result.append(call.args[0].value)
        return result

    @property
    def sources(self) -> list[tuple[str, str]]:
        """Return list of (source_name, table_name) tuples from source() calls."""
        result = []
        for call in self._find_calls('source'):
            if len(call.args) != 2:
                logger.warning(f"Invalid source() call in {self.name}: expected 2 args, got {len(call.args)}")
                continue
            result.append((call.args[0].value, call.args[1].value))
        return result

