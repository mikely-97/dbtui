"""
Properties panel widget for displaying model property claims.

Shows the effective properties collected from dbt_project.yml, schema.yml,
and model config() calls, with visual indication of the property source.
"""
from typing import TYPE_CHECKING

from textual.widgets import Static, ListView, ListItem, Label
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

if TYPE_CHECKING:
    from ..common import DbtModel
    from ...backend.property_claim import PropertyClaim


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


class PropertyItem(ListItem):
    """A single property claim displayed in the properties panel."""

    def __init__(self, claim: 'PropertyClaim') -> None:
        super().__init__()
        self.claim = claim

    def compose(self):
        source_color = SOURCE_TYPE_COLORS.get(self.claim.source_type, "white")
        source_icon = SOURCE_TYPE_ICONS.get(self.claim.source_type, "•")

        value_display = self._format_value(self.claim.value)
        kind_indicator = "[config]" if self.claim.kind == "config" else "[prop]"

        yield Horizontal(
            Label(f"{source_icon} ", classes="property-icon"),
            Label(f"{self.claim.name}", classes="property-name"),
            Label(f" = ", classes="property-equals"),
            Label(f"{value_display}", classes="property-value"),
            Label(f" [{self.claim.source_type}]", classes="property-source"),
        )

    def _format_value(self, value) -> str:
        """Format property value for display."""
        if isinstance(value, str):
            if len(value) > 40:
                return f'"{value[:37]}..."'
            return f'"{value}"'
        elif isinstance(value, list):
            if len(value) > 3:
                return f"[{len(value)} items]"
            return str(value)
        elif isinstance(value, dict):
            return f"{{...}} ({len(value)} keys)"
        else:
            return str(value)


class PropertiesPanel(Vertical):
    """
    Panel displaying the effective properties for a model.

    Shows property claims from all sources with visual differentiation:
    - Green: Model-level config() (highest precedence)
    - Cyan: schema.yml properties
    - Yellow: dbt_project.yml configs (lowest precedence)
    """

    DEFAULT_CSS = """
    PropertiesPanel {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }

    PropertiesPanel > #properties-header {
        height: 3;
        text-style: bold;
        content-align: center middle;
        background: $surface;
    }

    PropertiesPanel > #properties-list {
        height: 1fr;
    }

    PropertiesPanel PropertyItem {
        height: 1;
        padding: 0;
    }

    PropertiesPanel .property-name {
        text-style: bold;
        color: $text;
    }

    PropertiesPanel .property-value {
        color: $secondary;
    }

    PropertiesPanel .property-source {
        color: $text-muted;
    }

    PropertiesPanel #no-properties {
        text-align: center;
        color: $text-muted;
        padding: 2;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "down", show=False),
        Binding("k", "cursor_up", "up", show=False),
    ]

    def __init__(self, model: 'DbtModel | None' = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._model = model

    def compose(self):
        yield Static("Properties", id="properties-header")
        yield ListView(id="properties-list")

    def on_mount(self) -> None:
        if self._model:
            self.update_properties(self._model)

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
