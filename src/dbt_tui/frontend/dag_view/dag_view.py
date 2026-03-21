from textual.app import ComposeResult
from textual.widgets import Static, Footer
from textual.containers import ScrollableContainer
from textual.binding import Binding

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.dag import render_dag_ascii


class DagView(DbtTuiScreen):
    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('+', 'increase_depth', 'More depth'),
        Binding('-', 'decrease_depth', 'Less depth'),
    ]

    def __init__(self):
        super().__init__()
        self._depth = 2

    def compose(self) -> ComposeResult:
        yield Static('', id='dag-title')
        yield Static('depth: 2  (+ / - to change)', id='dag-controls')
        yield ScrollableContainer(Static('', id='dag-content'))
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_dag()

    def on_model_change(self, model) -> None:
        self._refresh_dag()

    def _refresh_dag(self) -> None:
        model = self.app.model
        project = self.app.project
        controls = self.query_one('#dag-controls', Static)
        controls.update(f'depth: {self._depth}  (+ / - to change)')
        content = self.query_one('#dag-content', Static)
        if model is None or project is None:
            content.update('No model selected — press f to search.')
            return
        title = self.query_one('#dag-title', Static)
        title.update(f'DAG: {model.name}')
        text = render_dag_ascii(project, model, depth=self._depth)
        content.update(text)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_increase_depth(self) -> None:
        self._depth = min(self._depth + 1, 6)
        self._refresh_dag()

    def action_decrease_depth(self) -> None:
        self._depth = max(self._depth - 1, 0)
        self._refresh_dag()
