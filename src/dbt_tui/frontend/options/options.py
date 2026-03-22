"""
Options screen for configuring dbt-tui settings.

Settings are persisted to the cache file automatically.
"""
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Input, Label, Static

from ..common import DbtModel, DbtProject, DbtTuiScreen

if TYPE_CHECKING:
    from ..main import DbtTuiFrontend


class Options(DbtTuiScreen):
    """Options screen for configuring application settings."""

    app: 'DbtTuiFrontend'

    CSS = """
    Options {
        align: center middle;
    }

    Options > Container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    Options .header {
        text-style: bold;
        text-align: center;
        padding-bottom: 1;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }

    Options .option-group {
        height: auto;
        padding: 1 0;
    }

    Options .option-label {
        padding-bottom: 0;
    }

    Options .option-description {
        color: $text-muted;
        padding-bottom: 0;
    }

    Options Input {
        margin: 0;
    }

    Options .button-row {
        padding-top: 1;
        border-top: solid $primary;
        margin-top: 1;
    }

    Options Button {
        width: 100%;
    }

    Options .info-section {
        padding-top: 1;
        border-top: dashed $primary;
        margin-top: 1;
    }

    Options .info-label {
        color: $text-muted;
    }

    Options .info-value {
        padding-left: 2;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "close"),
        Binding("q", "close", "close", show=False),
    ]

    def compose(self):
        with Container():
            yield Static("Options", classes="header")

            # External editor option
            with Vertical(classes="option-group"):
                yield Label("External Editor", classes="option-label")
                yield Static(
                    "Command to open models in external editor (E key)",
                    classes="option-description"
                )
                yield Input(
                    value=self.app.external_editor_command,
                    placeholder="e.g., vim, code, nano",
                    id="external-editor-input"
                )

            # Info section - read-only info about current state
            with Vertical(classes="info-section"):
                yield Static("Current Session", classes="option-label")

                with Horizontal():
                    yield Label("Project:", classes="info-label")
                    project_name = self.app.project.root_folder.name if self.app.project else "None"
                    yield Static(project_name, classes="info-value", id="project-info")

                with Horizontal():
                    yield Label("Model:", classes="info-label")
                    model_name = self.app.model.name if self.app.model else "None"
                    yield Static(model_name, classes="info-value", id="model-info")

                with Horizontal():
                    yield Label("Logs:", classes="info-label")
                    from ...common import get_logs_dir
                    yield Static(str(get_logs_dir()), classes="info-value")

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Close", id="close-btn")

        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "external-editor-input":
            self.app.external_editor_command = event.value
            self.app.notify(f"External editor set to: {event.value}")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Save changes as user types (with debounce from app)."""
        if event.input.id == "external-editor-input":
            self.app.external_editor_command = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-btn":
            self.action_close()

    def action_close(self) -> None:
        """Close the options screen."""
        self.app.pop_screen()

    def on_model_change(self, model: DbtModel | None):
        """Update model info display when model changes."""
        try:
            model_info = self.query_one("#model-info", Static)
            model_info.update(model.name if model else "None")
        except Exception:
            pass

    def on_project_change(self, project: DbtProject | None):
        """Update project info display when project changes."""
        try:
            project_info = self.query_one("#project-info", Static)
            project_info.update(project.root_folder.name if project else "None")
        except Exception:
            pass
