from pathlib import Path
import json
from dataclasses import dataclass, field, asdict

from platformdirs import user_cache_dir


@dataclass
class WorkspaceEntry:
    project_path: str
    last_model: str | None = None


@dataclass
class DbtTuiCache:
    """Cache for persisting application state between sessions."""

    last_open_project_raw: str | None = None
    last_active_model: str | None = None
    external_editor_command: str = 'vi'
    workspaces: list[WorkspaceEntry] = field(default_factory=list)
    bookmarks: list[str] = field(default_factory=list)

    @property
    def last_open_project(self) -> Path | None:
        """Get the last opened project as a Path."""
        if self.last_open_project_raw is None:
            return None
        return Path(self.last_open_project_raw)

    @last_open_project.setter
    def last_open_project(self, value: str | Path | None):
        """Set the last opened project from a string or Path."""
        if value is None:
            self.last_open_project_raw = None
        elif isinstance(value, Path):
            self.last_open_project_raw = str(value)
        else:
            self.last_open_project_raw = value

def ensure_cache_path() -> Path:
    cache_dir = Path(user_cache_dir("dbt-tui"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / 'cache.json'

def create_empty_cache(cache_path: Path):
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(DbtTuiCache()), f)

def load_cache(clear_cache:bool=False) -> DbtTuiCache:
    cache_path = ensure_cache_path()
    if clear_cache or not cache_path.exists():
       create_empty_cache(cache_path)
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_raw = json.load(f)
    except json.JSONDecodeError:
        create_empty_cache(cache_path)
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_raw = json.load(f)
    workspaces = [WorkspaceEntry(**w) for w in cache_raw.pop('workspaces', [])]
    bookmarks = cache_raw.pop('bookmarks', [])
    dbt_tui_cache = DbtTuiCache(**cache_raw, workspaces=workspaces, bookmarks=bookmarks)
    return dbt_tui_cache

def save_cache(cache: DbtTuiCache):
    cache_path = ensure_cache_path()
    data = {
        'last_open_project_raw': cache.last_open_project_raw,
        'last_active_model': cache.last_active_model,
        'external_editor_command': cache.external_editor_command,
        'workspaces': [
            {'project_path': w.project_path, 'last_model': w.last_model}
            for w in cache.workspaces
        ],
        'bookmarks': cache.bookmarks,
    }
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)



