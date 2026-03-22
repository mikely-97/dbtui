from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Input, Static

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen

_SOURCE_LABELS = {
    'dbt_project.yml': 'project',
    'schema.yml': 'schema',
    'model': 'model.sql',
}


class PropertyViewerScreen(DbtTuiScreen):
    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('/', 'focus_filter', 'Filter'),
    ]

    def compose(self) -> ComposeResult:
        yield Static('', id='pv-header')
        yield Input(placeholder='Filter properties...', id='pv-filter')
        yield DataTable(id='pv-table', cursor_type='row')
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#pv-table', DataTable)
        table.add_columns('Property', 'Effective Value', 'Source', 'File', 'Overrides')
        self._refresh()

    def on_model_change(self, model) -> None:
        self._refresh()

    def _refresh(self) -> None:
        model = self.app.model
        header = self.query_one('#pv-header', Static)
        table = self.query_one('#pv-table', DataTable)
        table.clear()

        if model is None:
            header.update('No model selected — press f to search.')
            return

        header.update(f'Properties: {model.name}')
        filter_text = self.query_one('#pv-filter', Input).value.lower()

        aggregate = model.property_claims
        if aggregate is None:
            header.update(f'Properties: {model.name} (no claims loaded)')
            return
        effective = aggregate.effective      # dict[str, PropertyClaim]
        overridden = aggregate.overridden    # dict[str, list[PropertyClaim]]

        for prop_name in sorted(effective.keys()):
            if filter_text and filter_text not in prop_name.lower():
                continue
            claim = effective[prop_name]
            source_label = _SOURCE_LABELS.get(claim.source_type, claim.source_type)
            file_name = claim.source_path.name if claim.source_path else ''
            override_list = overridden.get(prop_name, [])
            override_count = str(len(override_list)) if override_list else ''
            value_str = str(claim.value)[:60]
            table.add_row(
                prop_name,
                value_str,
                source_label,
                file_name,
                override_count,
                key=prop_name,
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_focus_filter(self) -> None:
        self.query_one('#pv-filter', Input).focus()
