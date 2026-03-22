"""
Properties panel widget for displaying model property claims.

Shows the effective properties collected from dbt_project.yml, schema.yml,
and model config() calls, with visual indication of the property source.
"""
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static

from ...backend.property_writer import (
    WriteResult,
    write_property_to_model_sql,
    write_property_to_schema,
)
from .properties_formatter import (
    format_current_value,
    format_full_value,
    format_item_value,
    format_short_value,
    parse_value,
)

if TYPE_CHECKING:
    from ...backend.property_claim import PropertyClaim
    from ..common import DbtModel


SOURCE_TYPE_COLORS = {
    "model": "green",
    "schema.yml": "cyan",
    "dbt_project.yml": "yellow",
}

SOURCE_TYPE_ICONS = {
    "model": "📄",
    "schema.yml": "📋",
    "dbt_project.yml": "📦",
}


class PropertyDetailModal(ModalScreen[str | None]):
    """Modal showing full property details including overridden claims.

    Returns:
        "edit" if user wants to edit the property
        None if user just closed the modal
    """

    CSS_PATH = "properties_panel.tcss"

    BINDINGS = [
        Binding("escape", "close", "close"),
        Binding("e", "edit", "edit"),
    ]

    def __init__(self, claim: 'PropertyClaim', overridden: list['PropertyClaim'], **kwargs):
        super().__init__(**kwargs)
        self.claim = claim
        self.overridden = overridden
        self._is_editable = claim.source_type != "dbt_project.yml"

    def compose(self):
        editable_indicator = "" if self._is_editable else " (read-only)"
        with Container():
            yield Static(f"Property: {self.claim.name}{editable_indicator}", classes="modal-header")
            with Horizontal(classes="detail-row"):
                yield Label("Source:", classes="detail-label")
                yield Label(f"{self.claim.source_type}", classes="detail-value")
            with Horizontal(classes="detail-row"):
                yield Label("Kind:", classes="detail-label")
                yield Label(f"{self.claim.kind}", classes="detail-value")
            with Horizontal(classes="detail-row"):
                yield Label("Path:", classes="detail-label")
                yield Label(f"{self.claim.source_path.name}", classes="detail-value")
            yield Static("Value:", classes="detail-label")
            yield Static(format_full_value(self.claim.value), classes="value-full")

            if self.overridden:
                yield Static(f"Overrides ({len(self.overridden)}):", classes="overrides-header")
                for override in self.overridden:
                    yield Static(
                        f"  {override.source_type}: {format_short_value(override.value)}",
                        classes="override-item"
                    )

            with Horizontal(classes="button-row"):
                if self._is_editable:
                    yield Button("Edit", variant="primary", id="edit-btn")
                yield Button("Close", id="close-btn")



    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "edit-btn":
            self.dismiss("edit")
        else:
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)

    def action_edit(self) -> None:
        """Edit the property if editable."""
        if self._is_editable:
            self.dismiss("edit")
        else:
            self.app.notify("This property is read-only (from dbt_project.yml)", severity="warning")


class PropertyEditModal(ModalScreen[WriteResult | None]):
    """Modal for editing a property value."""

    CSS_PATH = "properties_panel.tcss"

    BINDINGS = [
        Binding("escape", "cancel", "cancel"),
    ]

    def __init__(self, claim: 'PropertyClaim', model: 'DbtModel', **kwargs):
        super().__init__(**kwargs)
        self.claim = claim
        self.model = model

    def compose(self):
        with Container():
            yield Static(f"Edit: {self.claim.name}", classes="modal-header")
            yield Static(
                f"Source: {self.claim.source_type} ({self.claim.source_path.name})",
                classes="info-row"
            )
            yield Input(
                value=format_current_value(self.claim.value),
                placeholder="Enter new value",
                id="value-input"
            )
            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._save_property()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Save on Enter key in input."""
        self._save_property()

    def _save_property(self) -> None:
        """Save the edited property."""
        new_value = self.query_one("#value-input", Input).value
        parsed_value = parse_value(new_value)

        if self.claim.source_type == "schema.yml":
            result = write_property_to_schema(
                self.model,
                self.claim.name,
                parsed_value,
                self.claim.kind,
                self.claim.source_path
            )
        elif self.claim.source_type == "model":
            result = write_property_to_model_sql(
                self.model,
                self.claim.name,
                parsed_value
            )
        else:
            result = WriteResult(False, "Cannot edit dbt_project.yml properties")

        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)


class AddPropertyModal(ModalScreen[WriteResult | None]):
    """Modal for adding a new property."""

    CSS_PATH = "properties_panel.tcss"

    BINDINGS = [
        Binding("escape", "cancel", "cancel"),
    ]

    LOCATION_OPTIONS = [
        ("schema.yml (config)", "schema_config"),
        ("schema.yml (property)", "schema_property"),
        ("model_name.yml (config)", "model_yml_config"),
        ("model_name.yml (property)", "model_yml_property"),
        ("Model SQL config()", "model_config"),
    ]

    def __init__(self, model: 'DbtModel', **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def compose(self):
        with Container():
            yield Static("Add New Property", classes="modal-header")
            yield Input(placeholder="Property name", id="name-input")
            yield Input(placeholder="Property value", id="value-input")
            yield Select(
                [(label, value) for label, value in self.LOCATION_OPTIONS],
                prompt="Where to define:",
                id="location-select",
                value="schema_config",
            )
            yield Static("", id="file-conflict", classes="file-conflict")
            yield Input(placeholder="Custom filename (e.g. my_models.yml)", id="custom-path-input")
            yield Static("", id="override-warning", classes="override-warning")
            with Horizontal(classes="button-row"):
                yield Button("Add", variant="primary", id="add-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        """Check for file conflicts on mount."""
        self._check_file_conflict()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Check for file conflicts when location changes."""
        self._check_file_conflict()

    def _check_file_conflict(self) -> None:
        """Check if model_name.yml already exists and show conflict UI."""
        location_select = self.query_one("#location-select", Select)
        conflict_label = self.query_one("#file-conflict", Static)
        custom_input = self.query_one("#custom-path-input", Input)

        location = location_select.value
        if location in ("model_yml_config", "model_yml_property"):
            model_yml_path = self.model.file_path_full.parent / f"{self.model.name}.yml"
            if model_yml_path.exists():
                conflict_label.update(
                    f"⚠ {self.model.name}.yml exists. Enter custom name or leave empty to append."
                )
                custom_input.add_class("visible")
            else:
                conflict_label.update(f"Will create: {self.model.name}.yml")
                custom_input.remove_class("visible")
        else:
            conflict_label.update("")
            custom_input.remove_class("visible")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Check for existing property when name changes."""
        if event.input.id == "name-input":
            self._check_override(event.value)

    def _check_override(self, prop_name: str) -> None:
        """Show warning if property already exists."""
        warning = self.query_one("#override-warning", Static)
        if not prop_name:
            warning.update("")
            return

        existing = self.model.property_claims.get_claim(prop_name) if self.model.property_claims else None
        if existing:
            warning.update(f"Warning: Will override existing value from {existing.source_type}")
        else:
            warning.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self._add_property()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Move focus or submit on Enter."""
        if event.input.id == "name-input":
            self.query_one("#value-input", Input).focus()
        elif event.input.id == "value-input":
            self._add_property()

    def _add_property(self) -> None:
        """Add the new property."""
        name = self.query_one("#name-input", Input).value.strip()
        value = self.query_one("#value-input", Input).value
        location = self.query_one("#location-select", Select).value
        custom_path = self.query_one("#custom-path-input", Input).value.strip()

        if not name:
            self.app.notify("Property name is required", severity="error")
            return

        parsed_value = parse_value(value)

        if location == "model_config":
            result = write_property_to_model_sql(self.model, name, parsed_value)
        elif location in ("model_yml_config", "model_yml_property"):
            # Determine the YAML file path
            if custom_path:
                # User provided custom filename
                if not custom_path.endswith(".yml"):
                    custom_path += ".yml"
                schema_path = self.model.file_path_full.parent / custom_path
            else:
                # Use model_name.yml
                schema_path = self.model.file_path_full.parent / f"{self.model.name}.yml"

            kind = "config" if location == "model_yml_config" else "property"
            result = write_property_to_schema(self.model, name, parsed_value, kind, schema_path)
        else:
            kind = "config" if location == "schema_config" else "property"
            result = write_property_to_schema(self.model, name, parsed_value, kind)

        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)


class PropertyItem(ListItem):
    """A single property claim displayed in the properties panel."""

    def __init__(self, claim: 'PropertyClaim') -> None:
        super().__init__()
        self.claim = claim

    def compose(self):
        source_icon = SOURCE_TYPE_ICONS.get(self.claim.source_type, "•")

        value_display = self._format_value(self.claim.value)

        yield Horizontal(
            Label(f"{source_icon} ", classes="property-icon"),
            Label(f"{self.claim.name}", classes="property-name"),
            Label(" = ", classes="property-equals"),
            Label(f"{value_display}", classes="property-value"),
            Label(f" [{self.claim.source_type}]", classes="property-source"),
        )

    def _format_value(self, value) -> str:
        """Format property value for display."""
        return format_item_value(value)


class PropertiesPanel(Vertical):
    """
    Panel displaying the effective properties for a model.

    Shows property claims from all sources with visual differentiation:
    - Green: Model-level config() (highest precedence)
    - Cyan: schema.yml properties
    - Yellow: dbt_project.yml configs (lowest precedence)
    """

    CSS_PATH = "properties_panel.tcss"

    BINDINGS = [
        Binding("down, j", "cursor_down", "down", show=False),
        Binding("up, k", "cursor_up", "up", show=False),
        Binding("enter", "show_property_details", "view"),
        Binding("e", "edit_property", "edit"),
        Binding("a", "add_property", "add"),
    ]

    can_focus = True

    def __init__(self, model: 'DbtModel | None' = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._model = model

    def compose(self):
        yield Static("Properties", id="properties-header")
        yield ListView(id="properties-list")

    def on_mount(self) -> None:
        if self._model:
            self.update_properties(self._model)

    def on_focus(self) -> None:
        """When panel receives focus, forward it to the properties list."""
        try:
            properties_list = self.query_one("#properties-list", ListView)
            properties_list.focus()
        except Exception:
            pass

    def update_properties(self, model: 'DbtModel | None') -> None:
        """Update the panel with properties from the given model."""
        self._model = model
        properties_list = self.query_one("#properties-list", ListView)
        properties_list.clear()

        if not model or not model.property_claims:
            properties_list.append(
                ListItem(Label("No properties found", id="no-properties"))
            )
            return

        # Get effective claims grouped by kind
        effective = model.property_claims.effective

        # Sort claims: configs first, then properties, alphabetically within each
        sorted_claims = sorted(
            effective.values(),
            key=lambda c: (0 if c.kind == "config" else 1, c.name)
        )

        for claim in sorted_claims:
            properties_list.append(PropertyItem(claim))

    def action_cursor_down(self) -> None:
        """Move cursor down in the properties list."""
        properties_list = self.query_one("#properties-list", ListView)
        properties_list.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the properties list."""
        properties_list = self.query_one("#properties-list", ListView)
        properties_list.action_cursor_up()

    def action_show_property_details(self) -> None:
        """Show details for the selected property."""
        properties_list = self.query_one("#properties-list", ListView)
        if properties_list.highlighted_child is None:
            return

        item = properties_list.highlighted_child
        if not isinstance(item, PropertyItem):
            return

        claim = item.claim
        overridden = self._model.property_claims.get_overridden_claims(claim.name) if self._model else []

        def handle_detail_result(result: str | None) -> None:
            if result == "edit" and self._model:
                self._open_edit_modal(claim)

        self.app.push_screen(PropertyDetailModal(claim, overridden), handle_detail_result)

    def _open_edit_modal(self, claim: 'PropertyClaim') -> None:
        """Open the edit modal for a property claim."""
        if not self._model:
            return

        def handle_result(result: WriteResult | None) -> None:
            if result and result.success:
                self.app.notify(result.message)
                self._refresh_properties()
            elif result and not result.success:
                self.app.notify(result.message, severity="error")

        self.app.push_screen(PropertyEditModal(claim, self._model), handle_result)

    def action_edit_property(self) -> None:
        """Edit the selected property directly."""
        properties_list = self.query_one("#properties-list", ListView)
        if properties_list.highlighted_child is None:
            return

        item = properties_list.highlighted_child
        if not isinstance(item, PropertyItem):
            return

        claim = item.claim

        # Check if editable
        if claim.source_type == "dbt_project.yml":
            self.app.notify("Cannot edit dbt_project.yml properties here", severity="warning")
            return

        self._open_edit_modal(claim)

    def _refresh_properties(self) -> None:
        """Recollect property claims and update the panel."""
        if not self._model:
            return

        from ...backend.property_claim import PropertyClaimAggregate
        from ...backend.property_discovery import collect_model_claims

        claims = collect_model_claims(self._model)
        aggregate = PropertyClaimAggregate(self._model)
        aggregate.add_all(claims)
        self._model.property_claims = aggregate

        self.update_properties(self._model)

    def action_add_property(self) -> None:
        """Add a new property."""
        if not self._model:
            self.app.notify("No model selected", severity="warning")
            return

        def handle_result(result: WriteResult | None) -> None:
            if result and result.success:
                self.app.notify(result.message)
                self._refresh_properties()
            elif result and not result.success:
                self.app.notify(result.message, severity="error")

        self.app.push_screen(AddPropertyModal(self._model), handle_result)
