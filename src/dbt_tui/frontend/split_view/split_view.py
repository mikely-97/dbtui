"""Split view — compare two models side by side."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Footer, TextArea, Input
from textual.containers import Horizontal, Vertical

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen


class SplitViewScreen(DbtTuiScreen):
    """Side-by-side comparison of two models."""

    DEFAULT_CSS = """
    SplitViewScreen #split-container { height: 1fr; }
    SplitViewScreen .split-pane { width: 1fr; border: solid $accent; }
    SplitViewScreen .split-header { height: 1; background: $accent; color: $text; }
    SplitViewScreen .split-search { height: 3; }
    SplitViewScreen TextArea { height: 1fr; }
    """

    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
    ]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static('Left: (current model)', id='left-header', classes='split-header'),
                TextArea(id='left-sql', read_only=True, language='sql', show_line_numbers=True),
                classes='split-pane',
            ),
            Vertical(
                Static('Right: type model name below', id='right-header', classes='split-header'),
                Input(id='right-search', placeholder='Type model name to compare...'),
                TextArea(id='right-sql', read_only=True, language='sql', show_line_numbers=True),
                classes='split-pane',
            ),
            id='split-container',
        )
        yield Footer()

    def on_mount(self) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        if model:
            left_header = self.query_one('#left-header', Static)
            left_header.update(f'Left: {model.name}')
            left_sql = self.query_one('#left-sql', TextArea)
            left_sql.load_text(model.text)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != 'right-search':
            return
        query = event.value.strip()
        if not query:
            return
        project = self.app.project  # type: ignore[attr-defined]
        if not project:
            return
        try:
            right_model = project.get_model_by_name(query)
            right_header = self.query_one('#right-header', Static)
            right_header.update(f'Right: {right_model.name}')
            right_sql = self.query_one('#right-sql', TextArea)
            right_sql.load_text(right_model.text)
        except Exception:
            # Model not found yet — user is still typing
            pass

    def on_model_change(self, model) -> None:
        if model:
            left_header = self.query_one('#left-header', Static)
            left_header.update(f'Left: {model.name}')
            left_sql = self.query_one('#left-sql', TextArea)
            left_sql.clear()
            left_sql.load_text(model.text)

    def action_go_back(self) -> None:
        self.app.pop_screen()
