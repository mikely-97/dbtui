from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Label, ListItem, ListView, Static

from dbt_tui.backend.dag import get_dag_node_list, get_execution_order, render_dag_ascii, render_dag_mermaid
from dbt_tui.backend.model import DbtModel
from dbt_tui.frontend.common.dbt_tui_screen import DbtTuiScreen


class DagView(DbtTuiScreen):
    DEFAULT_CSS = """
    DagView #dag-node-list { height: 8; border: solid $accent; }
    DagView #dag-nav-label { height: 1; color: $text-muted; }
    """

    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('+', 'increase_depth', 'More depth'),
        Binding('-', 'decrease_depth', 'Less depth'),
        Binding('m', 'export_mermaid', 'Mermaid'),
        Binding('x', 'toggle_exec_order', 'exec order'),
    ]

    def __init__(self):
        super().__init__()
        self._depth = 2
        self._nav_nodes: list = []
        self._show_exec_order = False

    def compose(self) -> ComposeResult:
        yield Static('', id='dag-title')
        yield Static('depth: 2  (+ / - to change)', id='dag-controls')
        yield ScrollableContainer(Static('', id='dag-content'))
        yield Static('Navigate (↑↓ Enter to jump):', id='dag-nav-label')
        yield ListView(id='dag-node-list')
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_dag()

    def on_model_change(self, model) -> None:
        self._refresh_dag()

    def _refresh_dag(self) -> None:
        model = self.app.model
        project = self.app.project
        controls = self.query_one('#dag-controls', Static)
        controls.update(f'depth: {self._depth}  (+ / - to change)')
        content = self.query_one('#dag-content', Static)
        node_list = self.query_one('#dag-node-list', ListView)

        if model is None or project is None:
            content.update('No model selected — press f to search.')
            node_list.clear()
            self._nav_nodes = []
            return

        title = self.query_one('#dag-title', Static)
        title.update(f'DAG: {model.name}')
        text = render_dag_ascii(project, model, depth=self._depth)
        content.update(text)

        # Populate navigation list
        if self._show_exec_order:
            self._nav_nodes = get_execution_order(project, model, depth=self._depth)
        else:
            self._nav_nodes = get_dag_node_list(project, model, depth=self._depth)

        node_list.clear()
        label_widget = self.query_one('#dag-nav-label', Static)
        mode = 'Execution order' if self._show_exec_order else 'Navigate'
        label_widget.update(f'{mode} (↑↓ Enter to jump):')

        for i, node in enumerate(self._nav_nodes):
            marker = '► ' if node is model else '  '
            if self._show_exec_order:
                label_text = f"{i+1}. {marker}{node.name} [{node.entity_type}]"
            else:
                label_text = f"{marker}{node.name} [{node.entity_type}]"
            node_list.append(ListItem(Label(label_text)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Navigate to the selected node when Enter is pressed."""
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._nav_nodes):
            target = self._nav_nodes[idx]
            if isinstance(target, DbtModel):
                self.app.model = target
            else:
                self.app.notify(f"Cannot navigate to {target.entity_type} '{target.name}'")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_increase_depth(self) -> None:
        self._depth = min(self._depth + 1, 6)
        self._refresh_dag()

    def action_decrease_depth(self) -> None:
        self._depth = max(self._depth - 1, 0)
        self._refresh_dag()

    def action_toggle_exec_order(self) -> None:
        self._show_exec_order = not self._show_exec_order
        self._refresh_dag()

    def action_export_mermaid(self) -> None:
        """Copy Mermaid diagram to clipboard or save to file."""
        model = self.app.model
        project = self.app.project
        if model is None or project is None:
            return
        mermaid = render_dag_mermaid(project, model, depth=self._depth)
        # Save to a temp file and notify
        import tempfile
        from pathlib import Path
        out = Path(tempfile.gettempdir()) / f'dag_{model.name}.mmd'
        out.write_text(mermaid)
        self.app.notify(f'Mermaid saved to {out}')
