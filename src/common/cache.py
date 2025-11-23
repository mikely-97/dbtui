from pathlib import Path
import json
from dataclasses import dataclass, asdict

from platformdirs import user_cache_dir

@dataclass
class dbtuiCache:
    """
    I am sure I kinda screwed up here
    and it is lowkey unreadable
    so # TODO refactor it
    """
    @property
    def last_open_project(self) -> Path|None:
        if self.last_open_project_raw is None:
            return None
        return Path(self.last_open_project_raw)
    
    @last_open_project.setter
    def last_open_project(self, value):
        if isinstance(value, str):
            self.last_open_project_raw = value
        elif isinstance(value, Path):
            self.last_open_project_raw = str(value)


    last_open_project_raw: Path|None=None
    last_active_model: str|None=None

def ensure_cache_path() -> Path:
    cache_dir = Path(user_cache_dir("dbtui"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def load_cache(clear_cache:bool=False) -> dbtuiCache:
    cache_path = ensure_cache_path() / 'cache.json'
    if clear_cache or not cache_path.exists():
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(dbtuiCache()), f)
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_raw = json.load(f)
    dbtui_cache = dbtuiCache(**cache_raw)
    return dbtui_cache

def save_cache(project_path: Path, model_name: str):
    cache_path = ensure_cache_path() / 'cache.json'
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(dbtuiCache(
            last_open_project_raw=str(project_path), 
            last_active_model=model_name)),
            f)



