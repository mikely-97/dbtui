from pathlib import Path
import json
from dataclasses import dataclass, asdict

from platformdirs import user_cache_dir


@dataclass
class dbtuiCache:
    """Cache for persisting application state between sessions."""

    last_open_project_raw: str | None = None
    last_active_model: str | None = None
    external_editor_command: str = 'vi'

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
    cache_dir = Path(user_cache_dir("dbtui"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def create_empty_cache(cache_path: Path):
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(dbtuiCache()), f)

def load_cache(clear_cache:bool=False) -> dbtuiCache:
    cache_path = ensure_cache_path() / 'cache.json'
    if clear_cache or not cache_path.exists():
       create_empty_cache(cache_path)
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_raw = json.load(f)
    except json.JSONDecodeError:
        create_empty_cache(cache_path)
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_raw = json.load(f)
    dbtui_cache = dbtuiCache(**cache_raw)
    return dbtui_cache

def save_cache(project_path: Path, model_name: str, external_editor_command: str):
    cache_path = ensure_cache_path() / 'cache.json'
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(
                asdict(
                    dbtuiCache(
                        last_open_project_raw=str(project_path) if project_path is not None else None,
                        last_active_model=model_name,
                        external_editor_command=external_editor_command,
                    )
                )
            ,f)



