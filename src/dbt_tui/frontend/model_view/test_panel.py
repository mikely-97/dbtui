"""Test results panel — runs dbt test and shows per-test pass/fail."""
from __future__ import annotations
import asyncio
import re
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Static
from textual.containers import Horizontal
from textual.widget import Widget
from textual import work

from dbt_tui.backend.runner import DbtRunner


@dataclass
class TestResult:
    name: str
    status: str          # PASS | FAIL | WARN | ERROR
    detail: str = ''


# Matches lines like:
#   PASS test_name ...... [PASS in 0.1s]
#   FAIL 1 test_name .... [FAIL in 0.2s]
#   WARN 3 test_name .... [WARN in 0.3s]
_LINE_RE = re.compile(
    r'^\s+(PASS|FAIL|WARN|ERROR)(?:\s+\d+)?\s+([\w.]+)',
    re.IGNORECASE,
)


def parse_test_results(lines: list[str]) -> list[TestResult]:
    """Parse dbt test stdout lines into structured TestResult objects."""
    results = []
    for line in lines:
        m = _LINE_RE.match(line)
        if m:
            status = m.group(1).upper()
            name = m.group(2)
            results.append(TestResult(name=name, status=status))
    return results


_STATUS_MARKUP = {
    'PASS': '[green]PASS[/green]',
    'FAIL': '[red]FAIL[/red]',
    'WARN': '[yellow]WARN[/yellow]',
    'ERROR': '[red bold]ERROR[/red bold]',
}


class TestPanel(Widget):
    DEFAULT_CSS = """
    TestPanel { height: 1fr; }
    TestPanel #test-controls { height: 3; }
    TestPanel Button { min-width: 14; }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Run Tests', id='btn-run-tests', variant='primary'),
            Button('Cancel', id='btn-cancel-tests', variant='error', disabled=True),
            Static('', id='test-status'),
            id='test-controls',
        )
        yield DataTable(id='test-table', zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one('#test-table', DataTable)
        table.add_columns('Test Name', 'Status')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-run-tests':
            self._start_tests()
        elif event.button.id == 'btn-cancel-tests':
            self.workers.cancel_all()

    def _start_tests(self) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        project = self.app.project  # type: ignore[attr-defined]
        if model is None or project is None:
            return
        self._set_running(True)
        table = self.query_one('#test-table', DataTable)
        table.clear()
        self._run_tests(model.name, project.root_folder)

    @work(exclusive=True, thread=False)
    async def _run_tests(self, select: str, project_path) -> None:
        status = self.query_one('#test-status', Static)
        table = self.query_one('#test-table', DataTable)
        runner = DbtRunner(project_path)
        lines: list[str] = []
        try:
            await runner.run(
                'test',
                select=select,
                on_line=lambda line: lines.append(line),
            )
        except asyncio.CancelledError:
            status.update('[yellow]Cancelled[/yellow]')
            return
        finally:
            self._set_running(False)

        results = parse_test_results(lines)
        if not results:
            status.update('[dim]No test results found[/dim]')
            return

        for r in results:
            markup = _STATUS_MARKUP.get(r.status, r.status)
            table.add_row(r.name, markup)

        passed = sum(1 for r in results if r.status == 'PASS')
        failed = sum(1 for r in results if r.status in ('FAIL', 'ERROR'))
        status.update(
            f'[green]{passed} passed[/green]  [red]{failed} failed[/red]'
            if failed else f'[green]All {passed} passed[/green]'
        )

    def _set_running(self, running: bool) -> None:
        self.query_one('#btn-run-tests', Button).disabled = running
        self.query_one('#btn-cancel-tests', Button).disabled = not running
        if running:
            self.query_one('#test-status', Static).update('[yellow]Running tests...[/yellow]')
