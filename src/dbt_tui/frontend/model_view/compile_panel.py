"""Compile panel — shows compiled SQL output from dbt compile."""
from __future__ import annotations
import asyncio
from textual.app import ComposeResult
from textual.widgets import Button, Static, TextArea
from textual.containers import Horizontal
from textual.widget import Widget
from textual import work

from dbt_tui.backend.runner import DbtRunner


class CompilePanel(Widget):
    DEFAULT_CSS = """
    CompilePanel { height: 1fr; }
    CompilePanel #compile-controls { height: 3; }
    CompilePanel Button { min-width: 14; }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Compile', id='btn-compile', variant='primary'),
            Button('Cancel', id='btn-cancel-compile', variant='error', disabled=True),
            Static('', id='compile-status'),
            id='compile-controls',
        )
        yield TextArea(id='compile-output', read_only=True, language='sql', show_line_numbers=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-compile':
            self._start_compile()
        elif event.button.id == 'btn-cancel-compile':
            self.workers.cancel_all()

    def _start_compile(self) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        project = self.app.project  # type: ignore[attr-defined]
        if model is None or project is None:
            return
        self._set_running(True)
        output = self.query_one('#compile-output', TextArea)
        output.clear()
        self._run_compile(model.name, project.root_folder)

    @work(exclusive=True, thread=False)
    async def _run_compile(self, select: str, project_path) -> None:
        status = self.query_one('#compile-status', Static)
        output = self.query_one('#compile-output', TextArea)
        runner = DbtRunner(project_path)
        lines: list[str] = []
        try:
            result = await runner.run(
                'compile',
                select=select,
                on_line=lambda line: lines.append(line),
            )
            if result.success:
                # dbt compile outputs compiled SQL mixed with status lines
                # Try to extract just the SQL portion
                sql_lines = _extract_compiled_sql(lines)
                output.load_text('\n'.join(sql_lines) if sql_lines else '\n'.join(lines))
                status.update('[green]Compiled[/green]')
            else:
                output.load_text('\n'.join(lines))
                status.update('[red]Failed[/red]')
        except asyncio.CancelledError:
            status.update('[yellow]Cancelled[/yellow]')
        finally:
            self._set_running(False)

    def _set_running(self, running: bool) -> None:
        self.query_one('#btn-compile', Button).disabled = running
        self.query_one('#btn-cancel-compile', Button).disabled = not running
        if running:
            self.query_one('#compile-status', Static).update('[yellow]Compiling...[/yellow]')


def _extract_compiled_sql(lines: list[str]) -> list[str]:
    """Extract compiled SQL from dbt compile output, skipping status/log lines."""
    sql_lines = []
    in_sql = False
    for line in lines:
        stripped = line.strip()
        # Skip dbt status lines
        if stripped.startswith(('Running with dbt', 'Found ', 'Concurrency:', 'Done.')):
            continue
        if stripped.startswith('--') or stripped == '':
            if in_sql:
                sql_lines.append(line)
            continue
        # Once we see actual SQL, start capturing
        in_sql = True
        sql_lines.append(line)
    return sql_lines
