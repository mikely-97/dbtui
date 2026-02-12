"""
Custom Textual messages for dbt-tui.

These messages allow screens to react to state changes in a decoupled way
using Textual's message system rather than direct method calls.
"""

from textual.message import Message
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .isolated import DbtModel, DbtProject


class ModelChanged(Message):
    """Message sent when the active model changes."""

    def __init__(self, model: 'DbtModel | None') -> None:
        self.model = model
        super().__init__()


class ProjectChanged(Message):
    """Message sent when the active project changes."""

    def __init__(self, project: 'DbtProject | None') -> None:
        self.project = project
        super().__init__()


class ModelFileChanged(Message):
    """Message sent when a model file is modified externally."""

    def __init__(self, model: 'DbtModel') -> None:
        self.model = model
        super().__init__()


class RefreshRequested(Message):
    """Message sent when a refresh is requested."""

    def __init__(self) -> None:
        super().__init__()
