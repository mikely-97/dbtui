"""
File watching module for detecting external changes to dbt project files.

Uses watchdog library to monitor file system changes and notify the application
when model files, schema files, or dbt_project.yml are modified.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from ..common.logging import get_logger

if TYPE_CHECKING:
    from .project import DbtProject

logger = get_logger('backend.file_watcher')


@dataclass
class FileChangeEvent:
    """Represents a file change event."""
    path: Path
    event_type: str  # 'modified', 'created', 'deleted'
    is_model: bool = False
    is_schema: bool = False
    is_project_yml: bool = False


class DbtProjectEventHandler(FileSystemEventHandler):
    """
    Handles file system events for a dbt project.

    Filters events to only notify about relevant file types:
    - .sql files (models)
    - schema.yml, _schema.yml, models.yml, _models.yml files
    - dbt_project.yml
    """

    def __init__(
        self,
        project: 'DbtProject',
        on_change: Callable[[FileChangeEvent], None],
    ):
        super().__init__()
        self.project = project
        self.on_change = on_change
        self._debounce_lock = threading.Lock()
        self._pending_events: dict[Path, FileChangeEvent] = {}

    def _is_relevant_file(self, path: Path) -> tuple[bool, bool, bool]:
        """
        Check if a file is relevant to the dbt project.

        Returns:
            Tuple of (is_model, is_schema, is_project_yml)
        """
        name = path.name.lower()
        suffix = path.suffix.lower()

        # Check if it's a model file
        is_model = suffix == '.sql'

        # Check if it's a schema file
        stem = path.stem.lower()
        is_schema = suffix in ('.yml', '.yaml') and stem in (
            'schema', '_schema', 'models', '_models'
        )

        # Check if it's the project file
        is_project_yml = name == 'dbt_project.yml'

        return is_model, is_schema, is_project_yml

    def _create_event(self, src_path: str, event_type: str) -> FileChangeEvent | None:
        """Create a FileChangeEvent if the file is relevant."""
        path = Path(src_path)
        is_model, is_schema, is_project_yml = self._is_relevant_file(path)

        if not any([is_model, is_schema, is_project_yml]):
            return None

        return FileChangeEvent(
            path=path,
            event_type=event_type,
            is_model=is_model,
            is_schema=is_schema,
            is_project_yml=is_project_yml,
        )

    def on_modified(self, event):
        if event.is_directory:
            return
        change_event = self._create_event(event.src_path, 'modified')
        if change_event:
            logger.debug(f"File modified: {change_event.path}")
            self.on_change(change_event)

    def on_created(self, event):
        if event.is_directory:
            return
        change_event = self._create_event(event.src_path, 'created')
        if change_event:
            logger.debug(f"File created: {change_event.path}")
            self.on_change(change_event)

    def on_deleted(self, event):
        if event.is_directory:
            return
        change_event = self._create_event(event.src_path, 'deleted')
        if change_event:
            logger.debug(f"File deleted: {change_event.path}")
            self.on_change(change_event)


class ProjectFileWatcher:
    """
    Watches a dbt project directory for file changes.

    Usage:
        def handle_change(event: FileChangeEvent):
            print(f"File changed: {event.path}")

        watcher = ProjectFileWatcher(project, on_change=handle_change)
        watcher.start()

        # ... later ...
        watcher.stop()

    The watcher runs in a background thread and calls the on_change callback
    whenever a relevant file is modified.
    """

    def __init__(
        self,
        project: 'DbtProject',
        on_change: Callable[[FileChangeEvent], None],
    ):
        self.project = project
        self.on_change = on_change
        self._observer: Observer | None = None
        self._running = False

    def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            return

        self._observer = Observer()
        handler = DbtProjectEventHandler(self.project, self.on_change)

        # Watch the project root directory recursively
        self._observer.schedule(
            handler,
            str(self.project.root_folder),
            recursive=True
        )

        self._observer.start()
        self._running = True
        logger.info(f"Started watching: {self.project.root_folder}")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._running or self._observer is None:
            return

        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
        self._running = False
        logger.info(f"Stopped watching: {self.project.root_folder}")

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    def __enter__(self) -> 'ProjectFileWatcher':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
