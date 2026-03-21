"""Schema.yml editor modal — edit description and tags for a model."""
from __future__ import annotations
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static
from textual.containers import Vertical, Horizontal

from dbt_tui.backend.property_writer import write_property_to_schema

if TYPE_CHECKING:
    from dbt_tui.backend.model import DbtModel


class SchemaEditorScreen(ModalScreen):
    """Modal for editing a model's description and tags in schema.yml."""

    DEFAULT_CSS = """
    SchemaEditorScreen {
        align: center middle;
    }
    SchemaEditorScreen #editor-dialog {
        width: 70;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    SchemaEditorScreen Label { margin-bottom: 0; }
    SchemaEditorScreen Input { margin-bottom: 1; }
    SchemaEditorScreen #editor-buttons { height: 3; margin-top: 1; }
    SchemaEditorScreen #editor-status { height: 1; color: $text-muted; }
    """

    def __init__(self, model: 'DbtModel'):
        super().__init__()
        self._model = model

    def _get_current_description(self) -> str:
        if self._model.property_claims is None:
            return ''
        try:
            desc = self._model.property_claims.get_value('description')
            return str(desc) if desc else ''
        except Exception:
            return ''

    def _get_current_tags(self) -> str:
        if self._model.property_claims is None:
            return ''
        try:
            tags = self._model.property_claims.get_value('tags')
            if isinstance(tags, list):
                return ', '.join(str(t) for t in tags)
            return str(tags) if tags else ''
        except Exception:
            return ''

    def compose(self) -> ComposeResult:
        with Vertical(id='editor-dialog'):
            yield Label(f'Edit schema.yml — [bold]{self._model.name}[/bold]')
            yield Label('Description:')
            yield Input(
                value=self._get_current_description(),
                id='input-description',
                placeholder='Model description...',
            )
            yield Label('Tags (comma-separated):')
            yield Input(
                value=self._get_current_tags(),
                id='input-tags',
                placeholder='tag1, tag2, tag3',
            )
            yield Static('', id='editor-status')
            yield Horizontal(
                Button('Save', id='btn-save', variant='success'),
                Button('Cancel', id='btn-cancel', variant='default'),
                id='editor-buttons',
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-cancel':
            self.dismiss(False)
        elif event.button.id == 'btn-save':
            self._save()

    def _save(self) -> None:
        status = self.query_one('#editor-status', Static)
        description = self.query_one('#input-description', Input).value.strip()
        tags_raw = self.query_one('#input-tags', Input).value.strip()

        tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []

        saved_any = False
        if description:
            result = write_property_to_schema(self._model, 'description', description, 'property')
            if not result.success:
                status.update(f'[red]Error: {result.message}[/red]')
                return
            saved_any = True

        if tags:
            result = write_property_to_schema(self._model, 'tags', tags, 'config')
            if not result.success:
                status.update(f'[red]Error: {result.message}[/red]')
                return
            saved_any = True

        if saved_any:
            status.update('[green]Saved![/green]')
            self.dismiss(True)
        else:
            status.update('[yellow]Nothing to save[/yellow]')
