"""Bookmarked models screen."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView


class BookmarksScreen(ModalScreen):
    """Shows bookmarked models for quick navigation."""

    DEFAULT_CSS = """
    BookmarksScreen { align: center middle; }
    BookmarksScreen #bm-dialog {
        width: 60; height: 70%; max-height: 30;
        border: thick $accent; background: $surface; padding: 1 2;
    }
    BookmarksScreen Label { text-style: bold; margin-bottom: 1; }
    BookmarksScreen ListView { height: 1fr; }
    """

    BINDINGS = [
        Binding('escape', 'dismiss', 'Close'),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='bm-dialog'):
            yield Label('Bookmarked Models  (Esc to close)')
            yield ListView(id='bm-list')

    def on_mount(self) -> None:
        bookmarks = self.app.get_bookmarks()  # type: ignore[attr-defined]
        project = self.app.project  # type: ignore[attr-defined]
        node_list = self.query_one('#bm-list', ListView)
        self._models = []
        if not project:
            return
        for name in bookmarks:
            try:
                model = project.get_model_by_name(name)
                self._models.append(model)
                node_list.append(ListItem(Label(f"★ {name}")))
            except Exception:
                # Model may have been deleted
                node_list.append(ListItem(Label(f"✗ {name} (not found)")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._models):
            self.app.model = self._models[idx]  # type: ignore[attr-defined]
            self.dismiss()
