"""Run panel for executing dbt commands on the current model."""
from __future__ import annotations
import asyncio
from textual.app import ComposeResult
from textual.widgets import Button, RichLog, Static
from textual.containers import Horizontal
from textual.widget import Widget
from textual import work

from dbt_tui.backend.runner import DbtRunner


class RunPanel(Widget):
    DEFAULT_CSS = """
    RunPanel { height: 1fr; }
    RunPanel #run-controls { height: 3; }
    RunPanel Button { min-width: 10; }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Run', id='btn-run', variant='success'),
            Button('Test', id='btn-test', variant='primary'),
            Button('Build', id='btn-build', variant='warning'),
            Button('Cancel', id='btn-cancel', variant='error', disabled=True),
            Static('', id='run-status'),
            id='run-controls',
        )
        yield RichLog(id='run-log', wrap=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case 'btn-run':
                self.start_run('run')
            case 'btn-test':
                self.start_run('test')
            case 'btn-build':
                self.start_run('build')
            case 'btn-cancel':
                self.workers.cancel_all()

    def start_run(self, command: str) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        project = self.app.project  # type: ignore[attr-defined]
        if model is None or project is None:
            return
        self._set_running(True)
        log = self.query_one('#run-log', RichLog)
        log.clear()
        log.write(f'[bold]► dbt {command} --select {model.name}[/bold]')
        self._execute(command, model.name, project.root_folder)

    @work(exclusive=True, thread=False)
    async def _execute(self, command: str, select: str, project_path) -> None:
        log = self.query_one('#run-log', RichLog)
        status = self.query_one('#run-status', Static)
        runner = DbtRunner(project_path)
        try:
            result = await runner.run(
                command,
                select=select,
                on_line=lambda line: log.write(line),
            )
            if result.success:
                status.update('[green]✓ Passed[/green]')
            else:
                status.update('[red]✗ Failed[/red]')
        except asyncio.CancelledError:
            status.update('[yellow]Cancelled[/yellow]')
        finally:
            self._set_running(False)

    def _set_running(self, running: bool) -> None:
        for btn_id in ('#btn-run', '#btn-test', '#btn-build'):
            self.query_one(btn_id, Button).disabled = running
        self.query_one('#btn-cancel', Button).disabled = not running
        if running:
            self.query_one('#run-status', Static).update('[yellow]Running...[/yellow]')
