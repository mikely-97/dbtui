"""Command palette provider for dbt-tui."""
from __future__ import annotations
from functools import partial
from typing import TYPE_CHECKING

from textual.command import Provider, Hits, Hit

if TYPE_CHECKING:
    from .main import DbtTuiFrontend


class DbtTuiCommands(Provider):
    """Provides dbt-tui commands to the command palette."""

    async def search(self, query: str) -> Hits:
        """Search for matching commands."""
        app = self.app

        commands = [
            ("Find Model", "Open model search", "push_screen('model_search')"),
            ("DAG View", "Show dependency graph", "push_screen('dag_view')"),
            ("Column Lineage", "Show column lineage", "push_screen('lineage_view')"),
            ("Property Viewer", "Full-screen properties", "push_screen('property_viewer')"),
            ("Recent Models", "Recently visited models", "push_screen('recent_models')"),
            ("Bookmarks", "Show bookmarked models", "push_screen('bookmarks')"),
            ("Help", "Keyboard shortcuts", "push_screen('help')"),
            ("Options", "Settings", "push_screen('options')"),
            ("Change Project", "Select a different project", "push_screen('project_search')"),
            ("Toggle Theme", "Switch dark/light mode", "toggle_dark"),
        ]

        matcher = self.matcher(query)
        for name, description, action in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(name),
                    partial(app.run_action, action),
                    help=description,
                )
