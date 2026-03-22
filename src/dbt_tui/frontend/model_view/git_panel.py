"""Git information panel."""
from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, RichLog, Static, TabbedContent, TabPane

from dbt_tui.backend.git import get_git_blame, get_git_log, get_git_status, get_file_diff

_STATUS_ICONS = {
    'clean': '✓ clean',
    'modified': '✎ modified',
    'staged': '● staged',
    'untracked': '? untracked',
    'unknown': '– (not in git)',
}


class GitPanel(Widget):
    DEFAULT_CSS = """
    GitPanel { height: 1fr; }
    GitPanel #git-status-bar { height: 1; padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        yield Static('', id='git-status-bar')
        with TabbedContent():
            with TabPane('Log', id='git-tab-log'):
                yield DataTable(id='git-log-table')
            with TabPane('Blame', id='git-tab-blame'):
                yield RichLog(id='git-blame-log', wrap=False)
            with TabPane('Diff', id='git-tab-diff'):
                yield RichLog(id='git-diff-log', wrap=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one('#git-log-table', DataTable)
        table.add_columns('Hash', 'Author', 'Date', 'Message')

    def refresh_model(self, model) -> None:
        if model is None:
            return
        self._load_git_info(model.file_path_full)

    @work(exclusive=True)
    async def _load_git_info(self, file_path) -> None:
        from pathlib import Path
        status = await get_git_status(Path(file_path))
        log_entries = await get_git_log(Path(file_path), n=15)
        blame_lines = await get_git_blame(Path(file_path))
        diff_output = await get_file_diff(Path(file_path))

        status_bar = self.query_one('#git-status-bar', Static)
        label = _STATUS_ICONS.get(status.state, status.state)
        status_bar.update(f'git: {label}')

        table = self.query_one('#git-log-table', DataTable)
        table.clear()
        for e in log_entries:
            table.add_row(e.hash, e.author, e.date, e.message)

        blame_log = self.query_one('#git-blame-log', RichLog)
        blame_log.clear()
        for bl in blame_lines:
            prefix = f'[dim]{bl.hash:7} {bl.author[:12]:12}[/dim] '
            blame_log.write(prefix + bl.content)

        diff_log = self.query_one('#git-diff-log', RichLog)
        diff_log.clear()
        if diff_output:
            diff_log.write('[bold]Uncommitted changes:[/bold]\n')
            for line in diff_output.splitlines():
                if line.startswith('+') and not line.startswith('+++'):
                    diff_log.write(f'[green]{line}[/green]\n')
                elif line.startswith('-') and not line.startswith('---'):
                    diff_log.write(f'[red]{line}[/red]\n')
                else:
                    diff_log.write(line + '\n')
        else:
            diff_log.write('[dim]No uncommitted changes[/dim]')
