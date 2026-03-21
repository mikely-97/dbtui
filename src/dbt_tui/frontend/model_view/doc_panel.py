"""Documentation panel widget."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Markdown, Static
from textual.containers import ScrollableContainer
from textual.widget import Widget

from dbt_tui.backend.docs import collect_docs


class DocPanel(Widget):
    DEFAULT_CSS = """
    DocPanel {
        border: solid $accent;
        height: 1fr;
    }
    DocPanel #doc-header {
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static('Documentation', id='doc-header')
        yield ScrollableContainer(Markdown('', id='doc-content'))

    def refresh_model(self, model) -> None:
        md = self.query_one('#doc-content', Markdown)
        if model is None:
            md.update('*No model selected.*')
            return
        docs = collect_docs(model)
        md.update(docs.to_markdown())
