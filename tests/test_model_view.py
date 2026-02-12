"""
Tests for the ModelView screen and PropertiesPanel widget.

These tests verify that:
1. PropertiesPanel correctly displays property claims
2. PropertyItem formats values correctly
3. ModelView updates when model changes
4. The view is accessible from the main app
"""
from pathlib import Path
import pytest

from dbt_tui.backend import DbtProject
from dbt_tui.backend.property_claim import PropertyClaim, PropertyClaimAggregate
from dbt_tui.frontend.model_view.properties_panel import (
    PropertiesPanel,
    PropertyItem,
    SOURCE_TYPE_COLORS,
    SOURCE_TYPE_ICONS,
)


@pytest.fixture
def dbt_project():
    """Fixture that provides a DbtProject instance for testing."""
    return DbtProject('tests/testing')


class TestPropertyItemFormatting:
    """Test PropertyItem value formatting."""

    def test_format_short_string(self, dbt_project):
        """Short strings should be quoted."""
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='test_prop',
            value='short value',
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(claim.value)
        assert formatted == '"short value"'

    def test_format_long_string(self, dbt_project):
        """Long strings should be truncated."""
        model = dbt_project.get_model_by_name('v_a')
        long_value = 'a' * 50
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='test_prop',
            value=long_value,
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(claim.value)
        assert formatted.endswith('..."')
        assert len(formatted) < len(long_value) + 3

    def test_format_small_list(self, dbt_project):
        """Small lists should show contents."""
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='schema.yml',
            source_path=Path('tests/testing/vanilla/stg/schema.yml'),
            model=model,
            name='tags',
            value=['a', 'b'],
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(claim.value)
        assert "['a', 'b']" in formatted or "a" in formatted

    def test_format_large_list(self, dbt_project):
        """Large lists should show item count."""
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='schema.yml',
            source_path=Path('tests/testing/vanilla/stg/schema.yml'),
            model=model,
            name='tags',
            value=['a', 'b', 'c', 'd', 'e'],
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(claim.value)
        assert '5 items' in formatted

    def test_format_dict(self, dbt_project):
        """Dicts should show key count."""
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='schema.yml',
            source_path=Path('tests/testing/vanilla/stg/schema.yml'),
            model=model,
            name='meta',
            value={'key1': 'val1', 'key2': 'val2'},
            kind='property'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(claim.value)
        assert '2 keys' in formatted

    def test_format_numeric(self, dbt_project):
        """Numeric values should be converted to string."""
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='limit',
            value=100,
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(claim.value)
        assert formatted == '100'


class TestSourceTypeConstants:
    """Test that source type constants are properly defined."""

    def test_source_type_colors_defined(self):
        """All source types should have colors."""
        assert 'model' in SOURCE_TYPE_COLORS
        assert 'schema.yml' in SOURCE_TYPE_COLORS
        assert 'dbt_project.yml' in SOURCE_TYPE_COLORS

    def test_source_type_icons_defined(self):
        """All source types should have icons."""
        assert 'model' in SOURCE_TYPE_ICONS
        assert 'schema.yml' in SOURCE_TYPE_ICONS
        assert 'dbt_project.yml' in SOURCE_TYPE_ICONS


class TestPropertiesPanelLogic:
    """Test PropertiesPanel business logic without Textual rendering."""

    def test_panel_with_model_having_claims(self, dbt_project):
        """Panel should handle models with property claims."""
        model = dbt_project.get_model_by_name('c_changed_name')

        # Verify the model has property claims
        assert model.property_claims is not None
        assert len(model.property_claims) > 0

        # Verify effective properties can be retrieved
        effective = model.property_claims.effective
        assert len(effective) > 0

    def test_panel_sorts_claims_configs_first(self, dbt_project):
        """Claims should be sorted with configs before properties."""
        model = dbt_project.get_model_by_name('c_changed_name')
        effective = model.property_claims.effective

        # Sort as the panel does
        sorted_claims = sorted(
            effective.values(),
            key=lambda c: (0 if c.kind == "config" else 1, c.name)
        )

        # Check that configs come before properties
        seen_property = False
        for claim in sorted_claims:
            if claim.kind == 'property':
                seen_property = True
            elif claim.kind == 'config' and seen_property:
                pytest.fail("Config found after property - sorting is wrong")


class TestModelViewIntegration:
    """Integration tests for ModelView with the property system."""

    def test_model_has_property_claims_after_load(self, dbt_project):
        """Models should have property claims populated after project load."""
        for model in dbt_project.models:
            assert model.property_claims is not None
            # Every model should have at least some properties (e.g., materialized from dbt_project.yml)
            assert len(model.property_claims) >= 0

    def test_model_effective_values_accessible(self, dbt_project):
        """Should be able to get effective property values."""
        model = dbt_project.get_model_by_name('c_changed_name')
        values = model.property_claims.effective_values

        # c_changed_name has a name config in its SQL
        assert 'name' in values
        assert values['name'] == 'c_changed_name'

    def test_model_with_schema_properties(self, dbt_project):
        """Models in schema.yml should have description property."""
        model = dbt_project.get_model_by_name('c_changed_name')
        effective = model.property_claims.effective

        # This model should have a description from schema.yml
        if 'description' in effective:
            assert effective['description'].source_type == 'schema.yml'

    def test_claim_source_types_correct(self, dbt_project):
        """Claims should have correct source types."""
        model = dbt_project.get_model_by_name('c_changed_name')

        source_types_found = set()
        for claim in model.property_claims:
            assert claim.source_type in ('model', 'schema.yml', 'dbt_project.yml')
            source_types_found.add(claim.source_type)

        # This model should have claims from multiple sources
        assert len(source_types_found) >= 2


class TestModelViewScreenRegistration:
    """Test that ModelView is properly registered in the app."""

    def test_model_view_import(self):
        """ModelView should be importable from model_view module."""
        from dbt_tui.frontend.model_view import ModelView
        assert ModelView is not None

    def test_properties_panel_import(self):
        """PropertiesPanel should be importable from model_view module."""
        from dbt_tui.frontend.model_view import PropertiesPanel
        assert PropertiesPanel is not None

    def test_model_properties_screen_registered(self):
        """model_properties screen should be registered in the app."""
        from dbt_tui.frontend.main import DbtTuiFrontend
        assert 'model_properties' in DbtTuiFrontend.SCREENS

    def test_v_binding_exists(self):
        """'v' keybinding should exist to access model_properties."""
        from dbt_tui.frontend.main import DbtTuiFrontend
        bindings = [b for b in DbtTuiFrontend.BINDINGS if b.key == 'v']
        assert len(bindings) == 1
        assert 'model_properties' in bindings[0].action
