"""Keyboard shortcut help modal."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label

ALL_BINDINGS: list[tuple[str, str, str]] = [
    ('Global', 'q', 'Quit'),
    ('Global', 'o', 'Options'),
    ('Global', 'f', 'Find model'),
    ('Global', 'p', 'Change project'),
    ('Global', 'g', 'Recent models'),
    ('Global', 'v', 'Property viewer'),
    ('Global', 'd', 'DAG view'),
    ('Global', 'l', 'Column lineage'),
    ('Global', 'B', 'Show bookmarks'),
    ('Global', 'T', 'Toggle dark/light theme'),
    ('Global', '?', 'This help screen'),
    ('Model View', 'r', 'Run model'),
    ('Model View', 't', 'Test model'),
    ('Model View', 'R', 'Refresh properties'),
    ('Model View', 'E', 'Open in external editor'),
    ('Model View', 'e', 'Edit schema.yml'),
    ('Model View', 'b', 'Toggle bookmark'),
    ('Model View', 'F', 'Format SQL (prettify)'),
    ('Model View', '→ / l', 'Focus properties panel'),
    ('Model View', '← / h', 'Focus SQL editor'),
    ('Model View', 'enter', 'Enter edit mode (in SQL editor)'),
    ('Model View', 'escape', 'Exit edit mode / save'),
    ('Model View', 'tab', 'Next pane'),
    ('DAG View', '+', 'Increase depth'),
    ('DAG View', '-', 'Decrease depth'),
    ('DAG View', 'm', 'Export Mermaid diagram'),
    ('DAG View', 'x', 'Toggle execution order'),
    ('DAG View', 'enter', 'Navigate to selected node'),
    ('DAG View', 'escape', 'Back'),
    ('Model Search', 'down / j', 'Next result'),
    ('Model Search', 'up / k', 'Previous result'),
    ('Model Search', 'enter', 'Select model'),
    ('Model Search', 'escape', 'Back'),
    ('Property Viewer', 'escape', 'Back'),
    ('Lineage View', 'escape', 'Back'),
]


class HelpScreen(ModalScreen):
    """Full shortcut reference."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen #help-dialog {
        width: 80;
        height: 80%;
        max-height: 50;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    HelpScreen Label {
        text-style: bold;
        margin-bottom: 1;
    }
    HelpScreen DataTable { height: 1fr; }
    """

    BINDINGS = [
        Binding('escape', 'dismiss_help', 'Close', show=True),
        Binding('?', 'dismiss_help', 'Close', show=False),
        Binding('q', 'dismiss_help', 'Close', show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='help-dialog'):
            yield Label('Keyboard Shortcuts  (Esc to close)')
            yield DataTable(id='help-table', zebra_stripes=True, show_cursor=False)

    def on_mount(self) -> None:
        table = self.query_one('#help-table', DataTable)
        table.add_columns('Context', 'Key', 'Action')
        for context, key, action in ALL_BINDINGS:
            table.add_row(context, f'[bold]{key}[/bold]', action)

    def action_dismiss_help(self) -> None:
        self.dismiss()
