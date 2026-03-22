"""Run panel for executing dbt commands on the current model."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, RichLog, Static

from dbt_tui.backend.runner import DbtRunner


@dataclass
class RunRecord:
    command: str
    select: str
    lines: list[str] = field(default_factory=list)
    success: bool = False
    timestamp: str = ''


class RunPanel(Widget):
    DEFAULT_CSS = """
    RunPanel { height: 1fr; }
    RunPanel #run-controls { height: 3; }
    RunPanel #run-history-nav { height: 3; }
    RunPanel Button { min-width: 10; }
    RunPanel #hist-counter { width: 10; content-align: center middle; }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._history: list[RunRecord] = []
        self._hist_idx: int = -1   # -1 = live view

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Run', id='btn-run', variant='success'),
            Button('Test', id='btn-test', variant='primary'),
            Button('Build', id='btn-build', variant='warning'),
            Button('Cancel', id='btn-cancel', variant='error', disabled=True),
            Static('', id='run-status'),
            id='run-controls',
        )
        yield Horizontal(
            Button('← Prev', id='btn-hist-prev', disabled=True),
            Static('live', id='hist-counter'),
            Button('Next →', id='btn-hist-next', disabled=True),
            id='run-history-nav',
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
            case 'btn-hist-prev':
                self._navigate_history(-1)
            case 'btn-hist-next':
                self._navigate_history(+1)

    def start_run(self, command: str) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        project = self.app.project  # type: ignore[attr-defined]
        if model is None or project is None:
            return
        # Return to live view before starting
        self._hist_idx = -1
        self._update_history_controls()
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
        record = RunRecord(
            command=command,
            select=select,
            timestamp=datetime.now().strftime('%H:%M:%S'),
        )
        try:
            result = await runner.run(
                command,
                select=select,
                on_line=lambda line: (log.write(line), record.lines.append(line)),
            )
            record.success = result.success
            if result.success:
                status.update('[green]✓ Passed[/green]')
            else:
                status.update('[red]✗ Failed[/red]')
        except asyncio.CancelledError:
            status.update('[yellow]Cancelled[/yellow]')
        finally:
            self._set_running(False)
            self._history.append(record)
            self._hist_idx = -1  # stay on live
            self._update_history_controls()

    def _navigate_history(self, delta: int) -> None:
        """Move through history. _hist_idx==-1 means live view."""
        if not self._history:
            return
        max_idx = len(self._history) - 1
        if self._hist_idx == -1:
            new_idx = max_idx if delta < 0 else -1
        else:
            new_idx = self._hist_idx + delta
            if new_idx > max_idx:
                new_idx = -1  # back to live
            elif new_idx < 0:
                new_idx = 0

        self._hist_idx = new_idx
        self._update_history_controls()
        self._render_history()

    def _render_history(self) -> None:
        log = self.query_one('#run-log', RichLog)
        status = self.query_one('#run-status', Static)
        if self._hist_idx == -1:
            status.update('')
            return
        record = self._history[self._hist_idx]
        log.clear()
        log.write(f'[bold dim]── History: dbt {record.command} --select {record.select} @ {record.timestamp} ──[/bold dim]')
        for line in record.lines:
            log.write(line)
        icon = '[green]✓[/green]' if record.success else '[red]✗[/red]'
        status.update(f'{icon} [dim]history[/dim]')

    def _update_history_controls(self) -> None:
        counter = self.query_one('#hist-counter', Static)
        prev_btn = self.query_one('#btn-hist-prev', Button)
        next_btn = self.query_one('#btn-hist-next', Button)

        n = len(self._history)
        if n == 0:
            counter.update('live')
            prev_btn.disabled = True
            next_btn.disabled = True
            return

        if self._hist_idx == -1:
            counter.update(f'live ({n})')
            prev_btn.disabled = False
            next_btn.disabled = True
        else:
            counter.update(f'{self._hist_idx + 1}/{n}')
            prev_btn.disabled = self._hist_idx == 0
            next_btn.disabled = False  # can always go forward to next or live

    def _set_running(self, running: bool) -> None:
        for btn_id in ('#btn-run', '#btn-test', '#btn-build'):
            self.query_one(btn_id, Button).disabled = running
        self.query_one('#btn-cancel', Button).disabled = not running
        if running:
            self.query_one('#run-status', Static).update('[yellow]Running...[/yellow]')
