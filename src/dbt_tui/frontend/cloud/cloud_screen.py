"""dbt Cloud integration screen."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Footer, DataTable, Input, Button
from textual.containers import Vertical, Horizontal
from textual import work

from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen
from dbt_tui.backend.cloud import DbtCloudClient, CloudConfig, STATUS_LABELS


class CloudScreen(DbtTuiScreen):
    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('r', 'refresh_runs', 'Refresh'),
    ]

    DEFAULT_CSS = """
    CloudScreen #cloud-config { height: 5; }
    CloudScreen Input { width: 40; }
    CloudScreen #cloud-status { height: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Static('dbt Cloud', id='cloud-title')
        yield Horizontal(
            Static('Token: '),
            Input(id='cloud-token', placeholder='dbt Cloud API token', password=True),
            Static(' Account ID: '),
            Input(id='cloud-account', placeholder='Account ID'),
            Button('Connect', id='btn-connect', variant='primary'),
            id='cloud-config',
        )
        yield Static('', id='cloud-status')
        yield DataTable(id='cloud-runs', zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#cloud-runs', DataTable)
        table.add_columns('Run ID', 'Job', 'Status', 'Duration', 'Created')
        # Load saved config
        from dbt_tui.common.cache import load_cache
        cache = load_cache()
        if cache.cloud_api_token:
            self.query_one('#cloud-token', Input).value = cache.cloud_api_token
        if cache.cloud_account_id:
            self.query_one('#cloud-account', Input).value = cache.cloud_account_id

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-connect':
            self._connect()

    def _connect(self) -> None:
        token = self.query_one('#cloud-token', Input).value.strip()
        account = self.query_one('#cloud-account', Input).value.strip()
        if not token or not account:
            self.query_one('#cloud-status', Static).update('[red]Token and Account ID required[/red]')
            return
        # Save config
        from dbt_tui.common.cache import load_cache, save_cache
        cache = load_cache()
        cache.cloud_api_token = token
        cache.cloud_account_id = account
        save_cache(cache)
        self._fetch_runs(token, account)

    @work(thread=True)
    def _fetch_runs(self, token: str, account: str) -> None:
        status = self.query_one('#cloud-status', Static)
        table = self.query_one('#cloud-runs', DataTable)
        client = DbtCloudClient(CloudConfig(api_token=token, account_id=account))
        try:
            runs = client.list_recent_runs(limit=20)
            self.app.call_from_thread(self._populate_runs, runs)
            self.app.call_from_thread(status.update, f'[green]Connected — {len(runs)} recent runs[/green]')
        except Exception as e:
            self.app.call_from_thread(status.update, f'[red]Error: {e}[/red]')

    def _populate_runs(self, runs) -> None:
        table = self.query_one('#cloud-runs', DataTable)
        table.clear()
        for run in runs:
            status_label = STATUS_LABELS.get(run.status, str(run.status))
            table.add_row(str(run.id), str(run.job_id), status_label, run.duration, run.created_at)

    def action_refresh_runs(self) -> None:
        self._connect()

    def action_go_back(self) -> None:
        self.app.pop_screen()
