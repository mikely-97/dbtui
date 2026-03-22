"""
Model view screen showing the active model content and its properties.

This view displays:
- Left panel: Model SQL content (editable)
- Right panel: Effective properties collected from all sources
"""
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, ListView, TabbedContent, TabPane, TextArea

from ..common import DbtModel, DbtProject, DbtTuiScreen
from .compile_panel import CompilePanel
from .doc_panel import DocPanel
from .git_panel import GitPanel
from .lint_panel import LintPanel
from .properties_panel import PropertiesPanel
from .run_panel import RunPanel
from .test_panel import TestPanel

if TYPE_CHECKING:
    from ..main import DbtTuiFrontend


class ModelView(DbtTuiScreen):
    """
    Screen showing the active model with its SQL content and properties.

    The view is split into two columns:
    - Left: Editable TextArea with the model's SQL code
    - Right: PropertiesPanel showing effective properties from all sources
    """

    app: 'DbtTuiFrontend'

    CSS_PATH = "model_view.tcss"

    BINDINGS = [
        Binding("E", "external_edit()", "edit externally"),
        Binding("tab", "focus_next", "next pane", show=False),
        Binding("shift+tab", "focus_previous", "prev pane", show=False),
        Binding("enter", "toggle_edit_mode()", "edit", show=False),
        Binding("escape", "exit_edit_mode()", "stop editing", show=False),
        Binding("R", "refresh_properties()", "refresh properties"),
        Binding("r", "run_model", "Run"),
        Binding("t", "test_model", "Test"),
        Binding("right, l", "focus_properties()", "properties", show=False),
        Binding("left, h", "focus_editor()", "editor", show=False),
        Binding("e", "edit_schema()", "edit schema"),
        Binding("b", "toggle_bookmark()", "bookmark"),
        Binding("F", "format_sql()", "format SQL"),
        Binding("X", "export_docs()", "export docs"),
    ]

    def compose(self):
        from textual.widgets import Static
        yield Horizontal(
            Vertical(
                Static(id="model-header"),
                ScrollableContainer(
                    TextArea(
                        id='model-content',
                        name='content',
                        read_only=True,
                        show_line_numbers=True,
                        language='sql',
                    )
                ),
                id="editor-container",
            ),
        )
        with TabbedContent():
            with TabPane("Properties", id="tab-props"):
                yield PropertiesPanel(id="properties-panel")
            with TabPane("Docs", id="tab-docs"):
                yield DocPanel(id="doc-panel")
            with TabPane("Git", id="tab-git"):
                yield GitPanel(id='git-panel')
            with TabPane("Run", id="tab-run"):
                yield RunPanel(id='run-panel')
            with TabPane("Tests", id="tab-tests"):
                yield TestPanel(id='test-panel')
            with TabPane("Compile", id="tab-compile"):
                yield CompilePanel(id='compile-panel')
            with TabPane("Lint", id="tab-lint"):
                yield LintPanel(id='lint-panel')
        yield Footer()

    def on_mount(self) -> None:
        self.on_model_change(self.app.model)
        # Set initial focus to the properties list
        self.action_focus_properties()

    def action_focus_properties(self) -> None:
        """Focus the properties panel."""
        try:
            properties_list = self.query_one("#properties-list", ListView)
            properties_list.focus()
        except Exception:
            pass

    def action_focus_editor(self) -> None:
        """Focus the editor."""
        try:
            textarea = self.query_one('#model-content', TextArea)
            textarea.focus()
        except Exception:
            pass

    def action_toggle_edit_mode(self) -> None:
        """Enter edit mode when pressing Enter on the TextArea."""
        textarea = self.query_one('#model-content', TextArea)
        if textarea.read_only and textarea.has_focus:
            textarea.read_only = False
            self.app.notify("Editing mode - press Escape to save and exit")

    async def action_exit_edit_mode(self) -> None:
        """Exit edit mode and save changes when pressing Escape."""
        textarea = self.query_one('#model-content', TextArea)
        if not textarea.read_only:
            textarea.read_only = True
            if self.app.model:
                # Use run_in_executor for file I/O to avoid blocking
                import asyncio
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.app.model.file_path_full.write_text,
                    textarea.text
                )
                self.app.notify("Changes saved")
                # Refresh properties after saving as config may have changed
                self._refresh_model_properties()
            textarea.blur()

    def action_run_model(self) -> None:
        self.query_one('#run-panel', RunPanel).start_run('run')

    def action_test_model(self) -> None:
        self.query_one('#run-panel', RunPanel).start_run('test')

    def action_edit_schema(self) -> None:
        """Open schema.yml editor for the current model."""
        if not self.app.model:
            return
        from .schema_editor import SchemaEditorScreen
        def on_dismiss(result: object) -> None:
            if result:
                self._refresh_model_properties()
                self.app.notify("schema.yml updated")
        self.app.push_screen(SchemaEditorScreen(self.app.model), on_dismiss)

    def action_toggle_bookmark(self) -> None:
        """Toggle bookmark for the current model."""
        if not self.app.model:
            return
        is_bookmarked = self.app.toggle_bookmark(self.app.model.name)
        icon = '★' if is_bookmarked else '☆'
        self.app.notify(f"{icon} {self.app.model.name}")

    def action_format_sql(self) -> None:
        """Format the model's SQL in the editor."""
        textarea = self.query_one('#model-content', TextArea)
        from dbt_tui.backend.formatter import format_sql
        formatted = format_sql(textarea.text)
        if formatted != textarea.text:
            textarea.clear()
            textarea.load_text(formatted)
            self.app.notify("SQL formatted")
        else:
            self.app.notify("No formatting changes")

    def action_export_docs(self) -> None:
        """Export model documentation as markdown."""
        if not self.app.model or not self.app.project:
            return
        from dbt_tui.backend.doc_export import export_model_markdown
        import tempfile
        from pathlib import Path
        md = export_model_markdown(self.app.project, self.app.model)
        out = Path(tempfile.gettempdir()) / f'{self.app.model.name}.md'
        out.write_text(md)
        self.app.notify(f'Docs exported to {out}')

    def action_refresh_properties(self) -> None:
        """Refresh the properties panel with recollected claims."""
        if self.app.model:
            self._refresh_model_properties()
            self.app.notify("Properties refreshed")

    def _refresh_model_properties(self) -> None:
        """Recollect property claims and update the panel."""
        if not self.app.model or not self.app.project:
            return

        # Recollect property claims for this model
        from ...backend.property_claim import PropertyClaimAggregate
        from ...backend.property_discovery import collect_model_claims

        claims = collect_model_claims(self.app.model)
        aggregate = PropertyClaimAggregate(self.app.model)
        aggregate.add_all(claims)
        self.app.model.property_claims = aggregate

        # Update the panel
        properties_panel = self.query_one('#properties-panel', PropertiesPanel)
        properties_panel.update_properties(self.app.model)

    def on_model_change(self, model: DbtModel | None) -> None:
        if not model:
            self.app.push_screen('model_search')
            return

        # Update header
        from textual.widgets import Static
        header = self.query_one('#model-header', Static)
        header.update(f"{model.name} ({model.file_path_relative})")

        # Check staleness
        from dbt_tui.backend.staleness import check_staleness
        if self.app.project:
            staleness = check_staleness(self.app.project, model)
            if staleness.is_stale:
                header.update(f"⚠ STALE {model.name} ({model.file_path_relative}) — modified parents: {', '.join(staleness.stale_parents)}")

        # Show last run result
        from dbt_tui.backend.run_results import get_model_run_result
        if self.app.project:
            run_result = get_model_run_result(self.app.project.root_folder, model.name)
            if run_result:
                status_icon = {'pass': '✓', 'success': '✓', 'fail': '✗', 'error': '✗'}.get(run_result.status, '?')
                current_header = str(header.renderable)
                header.update(f"{current_header}  [{status_icon} {run_result.status} {run_result.execution_time:.1f}s]")

        # Show manifest column types if available
        from dbt_tui.backend.manifest import get_manifest_node
        if self.app.project:
            manifest = get_manifest_node(self.app.project.root_folder, model.name)
            if manifest and manifest.compiled_code:
                # Update compile panel with cached compiled code
                try:
                    compile_panel = self.query_one('#compile-panel')
                    from .compile_panel import CompilePanel
                    if isinstance(compile_panel, CompilePanel):
                        compile_panel.update_compiled_code(manifest.compiled_code)
                except Exception:
                    pass

        # Update model content
        model_content = self.query_one('#model-content', TextArea)
        model_content.clear()
        model_content.load_text(model.text)

        # Update properties panel
        properties_panel = self.query_one('#properties-panel', PropertiesPanel)
        properties_panel.update_properties(model)

        # Update docs panel
        self.query_one('#doc-panel', DocPanel).refresh_model(model)

        # Update git panel
        self.query_one('#git-panel', GitPanel).refresh_model(model)

    def on_project_change(self, project: DbtProject | None) -> None:
        if project:
            self.app.push_screen('model_search')
