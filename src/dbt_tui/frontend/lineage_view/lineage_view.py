from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Footer
from textual.binding import Binding

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.lineage import extract_columns


class ColumnLineageView(DbtTuiScreen):
    BINDINGS = [Binding('escape', 'go_back', 'Back')]

    def compose(self) -> ComposeResult:
        yield Static('', id='lineage-header')
        yield DataTable(id='lineage-table', cursor_type='row')
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#lineage-table', DataTable)
        table.add_columns('Column', 'Source Model', 'Source Column', 'Expression')
        self._refresh()

    def on_model_change(self, model) -> None:
        self._refresh()

    def _refresh(self) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        header = self.query_one('#lineage-header', Static)
        table = self.query_one('#lineage-table', DataTable)
        table.clear()

        if model is None:
            header.update('No model selected.')
            return

        header.update(f'Column lineage: {model.name}')
        cols = extract_columns(model)

        if not cols:
            table.add_row('(no columns detected)', '', '', '')
            return

        for c in cols:
            table.add_row(
                c.name or '',
                c.source_model or '',
                c.source_column or '',
                c.source_expression or '',
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()
