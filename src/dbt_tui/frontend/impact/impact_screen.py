"""Impact analysis screen — shows what breaks if a model changes."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Footer, DataTable
from textual.containers import ScrollableContainer

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.impact import analyze_impact


class ImpactScreen(DbtTuiScreen):
    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
    ]

    def compose(self) -> ComposeResult:
        yield Static('', id='impact-title')
        yield Static('', id='impact-summary')
        yield DataTable(id='impact-table', zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_impact()

    def on_model_change(self, model) -> None:
        self._refresh_impact()

    def _refresh_impact(self) -> None:
        model = self.app.model
        project = self.app.project
        title = self.query_one('#impact-title', Static)
        summary = self.query_one('#impact-summary', Static)
        table = self.query_one('#impact-table', DataTable)

        if model is None or project is None:
            title.update('No model selected')
            return

        title.update(f'Impact Analysis: {model.name}')
        result = analyze_impact(project, model)

        if result.total_affected == 0:
            summary.update('[green]No downstream dependents — safe to change[/green]')
        else:
            summary.update(f'[yellow]Warning {result.total_affected} downstream entities affected[/yellow]')

        table.clear(columns=True)
        table.add_columns('Depth', 'Entity', 'Type')
        for depth, entities in result.by_depth.items():
            for entity in entities:
                table.add_row(str(depth), entity.name, entity.entity_type)

    def action_go_back(self) -> None:
        self.app.pop_screen()
