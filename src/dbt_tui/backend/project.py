import os
from pathlib import Path
import yaml
from typing import Generator
from networkx import DiGraph
import fnmatch
from difflib import SequenceMatcher


from ..common import DbtProjectAbstract, DbtEntityAbstract, EntityType, \
NonePathException, DbtModelNotFoundException, \
IncorrectFileExtensionException, NotWithinSubdirectoryException, \
InvalidProjectPathException, ErrorCollector, ErrorCategory
from ..common.logging import get_logger


from .model import DbtModel
from .macro import DbtMacro
from .property_claim import PropertyClaimAggregate
from .property_discovery import collect_model_claims_cached, PropertyDiscoveryCache
from .metrics import LoadMetrics, Timer


logger = get_logger('backend.project')


class DbtProject(DbtProjectAbstract):
    root_folder: Path
    dbt_project_yml: Generator
    model_folder: str
    full_models_paths: list[Path]
    full_macro_paths: list[Path]
    models: list[DbtModel]
    macros: list[DbtMacro]
    fall_back_to_filename: bool
    graph: DiGraph

    # optimizations for fetching models
    models_by_name: dict[str, DbtModel]
    models_by_file_name: dict[str, DbtModel]

    # optimizations for fetching macros
    macros_by_name: dict[str, DbtMacro]

    # performance metrics from last load
    load_metrics: LoadMetrics | None

    # error tracking for load issues
    load_errors: ErrorCollector

    def populate_graph(self):
        self.graph = DiGraph()
        # Add all macro nodes first
        for macro in self.macros:
            self.graph.add_node(macro)
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
                            msg = f"references '{ref}' which is not found as a name or filename"
                            logger.warning(f"{model.name} {msg}")
                            self.load_errors.add_ref_not_found(model.name, ref)
                    else:
                        msg = f"references '{ref}' which is not found as a name"
                        logger.warning(f"{model.name} {msg}")
                        self.load_errors.add_ref_not_found(model.name, ref)
                finally:
                    if referenced_model:
                        self.graph.add_node(referenced_model)
                        self.graph.add_edge(referenced_model, model)
            # Add macro dependency edges
            for macro_name in model.macro_calls:
                macro = self.macros_by_name.get(macro_name)
                if macro:
                    self.graph.add_edge(macro, model)

    def collect_property_claims(self) -> None:
        """
        Collect all PropertyClaims for all models in the project.

        This method creates a PropertyClaimAggregate for each model and populates
        it with claims from all sources (dbt_project.yml, schema.yml, model SQL).
        The aggregates handle precedence resolution lazily when accessed.

        Uses PropertyDiscoveryCache to read and parse YAML files only once,
        dramatically improving performance for projects with many models.
        """
        # Initialize cache once for all models
        cache = PropertyDiscoveryCache()
        cache.initialize(self)

        for model in self.models:
            aggregate = PropertyClaimAggregate(model)
            claims = collect_model_claims_cached(model, cache)
            aggregate.add_all(claims)
            model.property_claims = aggregate
    
    def reset_models(self) -> None:
        self.models = []
        self.models_by_name = dict()
        self.models_by_file_name = dict()
        self.macros = []
        self.macros_by_name = dict()


    def load_models(self) -> None:
        self.reset_models()
        for models_path in self.full_models_paths:
            if not models_path.exists():
                self.load_errors.add_warning(
                    f"Model path does not exist: {models_path}",
                    ErrorCategory.FILE_NOT_FOUND,
                    source_path=models_path,
                )
                continue
            for root, _, files in models_path.walk():
                for file in files:
                    # Only load SQL files as models
                    if not file.endswith('.sql'):
                        continue
                    file_path = root / file
                    try:
                        model = DbtModel(file_path, self)
                        self.models.append(model)
                        self.models_by_name[model.name] = model
                        self.models_by_file_name[model.file_name] = model
                    except Exception as e:
                        self.load_errors.add_error(
                            f"Failed to load model: {e}",
                            ErrorCategory.PARSE_ERROR,
                            source_path=file_path,
                            exception=e,
                        )
                        logger.warning(f"Failed to load model {file_path}: {e}")


    def load_macros(self) -> None:
        for macro_path in self.full_macro_paths:
            if not macro_path.exists():
                continue
            for root, _, files in macro_path.walk():
                for file in files:
                    if not file.endswith('.sql'):
                        continue
                    file_path = root / file
                    try:
                        macro = DbtMacro(file_path, self)
                        self.macros.append(macro)
                        self.macros_by_name[macro.name] = macro
                    except Exception as e:
                        logger.warning(f"Failed to load macro {file_path}: {e}")

    def refresh(self):
        if not os.path.exists(self.root_folder):
            raise FileNotFoundError("Folder not found: %s" % self.root_folder)

        total_timer = Timer()
        self.load_metrics = LoadMetrics()
        self.load_errors = ErrorCollector()

        try:
            with total_timer:
                # Parse dbt_project.yml
                with Timer() as t:
                    with open(self.root_folder / 'dbt_project.yml', 'r', encoding='utf-8') as f:
                        self.parse_dbt_project(f.read())
                self.load_metrics.parse_dbt_project_yml_ms = t.elapsed_ms

                # Load models
                with Timer() as t:
                    self.load_models()
                self.load_metrics.load_models_ms = t.elapsed_ms

                # Load macros
                with Timer() as t:
                    self.load_macros()
                self.load_metrics.load_models_ms += t.elapsed_ms  # piggyback on model timer

                # Build graph
                with Timer() as t:
                    self.populate_graph()
                self.load_metrics.populate_graph_ms = t.elapsed_ms

                # Collect property claims
                with Timer() as t:
                    self.collect_property_claims()
                self.load_metrics.collect_property_claims_ms = t.elapsed_ms

            self.load_metrics.total_load_ms = total_timer.elapsed_ms
            self.load_metrics.model_count = len(self.models)

            # Log load metrics at INFO level
            logger.info(f"Project loaded: {self.root_folder.name}")
            logger.info(f"  Models: {self.load_metrics.model_count}")
            logger.info(f"  Total: {self.load_metrics.total_load_ms:.1f}ms")
            if self.load_errors.has_any:
                logger.info(f"  Issues: {self.load_errors.summary()}")
            logger.debug(f"  - parse_dbt_project.yml: {self.load_metrics.parse_dbt_project_yml_ms:.1f}ms")
            logger.debug(f"  - load_models: {self.load_metrics.load_models_ms:.1f}ms")
            logger.debug(f"  - populate_graph: {self.load_metrics.populate_graph_ms:.1f}ms")
            logger.debug(f"  - collect_property_claims: {self.load_metrics.collect_property_claims_ms:.1f}ms")

        except FileNotFoundError:
            raise FileNotFoundError("dbt folder is present, but dbt_project.yml is not found: %s" % self.root_folder)


    def parse_dbt_project(self, dbt_project_raw: str) -> None:
        self.dbt_project_yml = yaml.load(dbt_project_raw, yaml.Loader)
        self.full_models_paths = [self.root_folder / folder for folder in self.dbt_project_yml['model-paths']]
        macro_paths = self.dbt_project_yml.get('macro-paths', ['macros'])
        self.full_macro_paths = [self.root_folder / folder for folder in macro_paths]

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

    # =========================================================================
    # Entity-generic methods (for future extensibility)
    # =========================================================================

    def get_entity_by_name(
        self,
        name: str,
        entity_type: EntityType | None = None
    ) -> DbtEntityAbstract:
        """
        Get an entity by name, optionally filtering by type.

        Currently only supports models, but designed for future extensibility
        to seeds, macros, etc.
        """
        # For now, only models are supported
        if entity_type is None or entity_type == "model":
            return self.get_model_by_name(name)

        raise DbtModelNotFoundException(f"Entity not found: {name} (type: {entity_type})")

    def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        path_prefix: str | None = None,
    ) -> list:
        """
        Search for entities matching a query, with optional filters.

        Args:
            query: Search query (fuzzy matching)
            entity_type: If provided, restrict to 'model' or 'macro'
            path_prefix: If provided, restrict to entities whose file_path_relative
                         contains this prefix string
        """
        from difflib import SequenceMatcher

        candidates = []
        if entity_type is None or entity_type == 'model':
            candidates.extend(self.models)
        if entity_type is None or entity_type == 'macro':
            candidates.extend(self.macros)

        if path_prefix:
            candidates = [
                c for c in candidates
                if path_prefix in str(c.file_path_relative)
            ]

        if not query:
            return sorted(candidates, key=lambda c: c.name)

        q = query.lower()

        def score(entity) -> float:
            name = entity.name.lower()
            if name == q:
                return 1.0
            if name.startswith(q):
                return 0.9 + len(q) / len(name) * 0.09
            if q in name:
                return 0.7 + len(q) / len(name) * 0.19
            return SequenceMatcher(None, q, name).ratio() * 0.6

        scored = [(score(c), c) for c in candidates]
        scored = [(s, c) for s, c in scored if s > 0.3]
        scored.sort(key=lambda x: (-x[0], x[1].name))
        return [c for _, c in scored]

    def search_models(self, query: str) -> list[DbtModel]:
        """Search models only, delegating to search_entities."""
        return [e for e in self.search_entities(query, entity_type='model')
                if isinstance(e, DbtModel)]

    def search_model(self, query: str, fuzzy_threshold: float = 0.6) -> list[DbtModel]:
        """
        Search for models using multiple strategies:
        1. Exact name match
        2. Glob/wildcard patterns (*, ?)
        3. Path prefix matching (path:models/staging)
        4. Tag matching (tag:my_tag) - if tags are available
        5. Fuzzy matching for typo tolerance

        Results are sorted by relevance (exact > glob > fuzzy).
        """
        query = query.strip()
        if not query:
            return []

        # 1. Try exact match first
        try:
            return [self.get_model_by_name(query)]
        except DbtModelNotFoundException:
            pass

        results: list[tuple[float, DbtModel]] = []  # (score, model)

        # 2. Check for dbt-style selectors
        if query.startswith('path:'):
            path_prefix = query[5:]
            for model in self.models:
                if model.file_path_relative.as_posix().startswith(path_prefix):
                    results.append((1.0, model))
            return [m for _, m in sorted(results, key=lambda x: x[1].name)]

        if query.startswith('tag:'):
            tag = query[4:]
            for model in self.models:
                if hasattr(model, 'tags') and tag in getattr(model, 'tags', []):
                    results.append((1.0, model))
            return [m for _, m in sorted(results, key=lambda x: x[1].name)]

        # 3. Glob/wildcard matching
        if '*' in query or '?' in query:
            for model in self.models:
                if fnmatch.fnmatch(model.name, query):
                    results.append((0.95, model))
            if results:
                return [m for _, m in sorted(results, key=lambda x: x[1].name)]

        # 4. Fuzzy matching
        query_lower = query.lower()
        for model in self.models:
            name_lower = model.name.lower()

            # Substring match (high priority)
            if query_lower in name_lower:
                # Score based on how much of the name is matched
                score = len(query_lower) / len(name_lower)
                results.append((0.9 + score * 0.1, model))
                continue

            # Fuzzy match using SequenceMatcher
            ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
            if ratio >= fuzzy_threshold:
                results.append((ratio, model))

        # Sort by score descending, then by name
        results.sort(key=lambda x: (-x[0], x[1].name))
        return [m for _, m in results]
        

    def __init__(self, project_path: Path|str, fall_back_to_filename: bool = False) -> None:
        if project_path is None:
            raise NonePathException("project_path is None")
        if isinstance(project_path, str):
            try:
                project_path = Path(project_path)
            except TypeError as e:
                raise InvalidProjectPathException(
                    f"Cannot convert '{project_path}' to a valid path: {e}"
                )
        self.fall_back_to_filename = fall_back_to_filename
        self.root_folder = project_path
        self.load_metrics = None
        self.load_errors = ErrorCollector()
        logger.debug(f"Initializing project: {project_path}")
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
        if filepath.is_absolute():
            # will raise an exception with required details if not a subfolder
            filepath.relative_to(self.root_folder)
            filepath_prepared = filepath
        else:
            filepath_prepared = self.root_folder / filepath

        if filepath_prepared.is_dir():
            raise IsADirectoryError(f"This filepath is an existing folder: {filepath_prepared.as_posix()}")
        if filepath_prepared.exists():
            raise FileExistsError(f"Another file exists at this path: {filepath_prepared.as_posix()}")
        if filepath.suffix != '.sql':
            raise IncorrectFileExtensionException(f"dbt models should be <.sql> files, but <{filepath.suffix}> given")

        if isinstance(from_, DbtModel):
            text = "SELECT * FROM {{ ref('%s') }}" % from_.name
        else:
            text = ''

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

        logger.info(f"Created new model: {filepath_prepared.stem}")
        self.refresh()

        return self.get_model_by_name(filepath_prepared.stem)
        


