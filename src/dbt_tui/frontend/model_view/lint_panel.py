"""SQL lint panel — shows lint warnings for the current model."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Static
from textual.containers import Horizontal
from textual.widget import Widget

from dbt_tui.backend.linter import lint_sql


class LintPanel(Widget):
    DEFAULT_CSS = """
    LintPanel { height: 1fr; }
    LintPanel #lint-controls { height: 3; }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Lint', id='btn-lint', variant='primary'),
            Static('', id='lint-status'),
            id='lint-controls',
        )
        yield DataTable(id='lint-table', zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one('#lint-table', DataTable)
        table.add_columns('Line', 'Code', 'Severity', 'Message')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-lint':
            self._run_lint()

    def _run_lint(self) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        if model is None:
            return
        table = self.query_one('#lint-table', DataTable)
        status = self.query_one('#lint-status', Static)
        table.clear()

        issues = lint_sql(model.text)
        if not issues:
            status.update('[green]No issues found[/green]')
            return

        errors = sum(1 for i in issues if i.severity == 'error')
        warnings = sum(1 for i in issues if i.severity == 'warning')

        for issue in issues:
            sev_markup = '[red]error[/red]' if issue.severity == 'error' else '[yellow]warn[/yellow]'
            table.add_row(str(issue.line), issue.code, sev_markup, issue.message)

        status.update(f'[red]{errors} errors[/red] [yellow]{warnings} warnings[/yellow]' if errors else f'[yellow]{warnings} warnings[/yellow]')
