"""Recently visited models screen."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import ListView, ListItem, Label
from textual.containers import Vertical


class RecentModelsScreen(ModalScreen):
    """Shows recently visited models for quick navigation."""

    DEFAULT_CSS = """
    RecentModelsScreen {
        align: center middle;
    }
    RecentModelsScreen #recent-dialog {
        width: 60;
        height: 70%;
        max-height: 30;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    RecentModelsScreen Label { text-style: bold; margin-bottom: 1; }
    RecentModelsScreen ListView { height: 1fr; }
    """

    BINDINGS = [
        Binding('escape', 'dismiss', 'Close'),
        Binding('g', 'dismiss', 'Close'),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='recent-dialog'):
            yield Label('Recent Models  (Esc to close)')
            yield ListView(id='recent-list')

    def on_mount(self) -> None:
        history = list(reversed(getattr(self.app, '_model_history', [])))
        node_list = self.query_one('#recent-list', ListView)
        self._nodes = history
        current = getattr(self.app, 'model', None)
        for model in history:
            marker = '► ' if model is current else '  '
            node_list.append(ListItem(Label(f"{marker}{model.name}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._nodes):
            self.app.model = self._nodes[idx]
            self.dismiss()
