"""
Tests for PropertyClaim precedence logic and property discovery.

These tests verify that:
1. PropertyClaim precedence comparison works correctly
2. Properties are discovered from all sources (dbt_project.yml, schema.yml, model SQL)
3. Precedence resolution returns the correct winning property
"""

from pathlib import Path
import pytest
from src.backend import DbtProject
from src.backend.property_claim import PropertyClaim
from src.backend.property_discovery import (
    collect_model_claims,
    collect_project_configs,
    collect_schema_properties,
    collect_sql_configs,
    resolve_property_precedence,
    find_schema_files,
)


@pytest.fixture
def dbt_project():
    """Fixture that provides a DbtProject instance for testing."""
    return DbtProject('tests/testing')


class TestPropertyClaimPrecedence:
    """Test PropertyClaim.__gt__ comparison logic for precedence."""

    def test_model_beats_schema(self, dbt_project):
        """Model-level config should have higher precedence than schema.yml."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claim_model = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='materialized',
            value='table',
            kind='config'
        )

        claim_schema = PropertyClaim(
            source_type='schema.yml',
            source_path=Path('tests/testing/complex_config/schema.yml'),
            model=model,
            name='materialized',
            value='view',
            kind='config'
        )

        assert claim_model > claim_schema

    def test_schema_beats_project(self, dbt_project):
        """schema.yml should have higher precedence than dbt_project.yml."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claim_schema = PropertyClaim(
            source_type='schema.yml',
            source_path=Path('tests/testing/complex_config/schema.yml'),
            model=model,
            name='materialized',
            value='view',
            kind='config'
        )

        claim_project = PropertyClaim(
            source_type='dbt_project.yml',
            source_path=Path('tests/testing/dbt_project.yml'),
            model=model,
            name='materialized',
            value='ephemeral',
            yaml_path='models.testing.complex_config.stg',
            effective=True,
            kind='config'
        )

        assert claim_schema > claim_project

    def test_more_specific_project_path_wins(self, dbt_project):
        """In dbt_project.yml, more specific paths should win."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claim_specific = PropertyClaim(
            source_type='dbt_project.yml',
            source_path=Path('tests/testing/dbt_project.yml'),
            model=model,
            name='materialized',
            value='table',
            yaml_path='models.testing.complex_config.stg',
            effective=True,
            kind='config'
        )

        claim_general = PropertyClaim(
            source_type='dbt_project.yml',
            source_path=Path('tests/testing/dbt_project.yml'),
            model=model,
            name='materialized',
            value='view',
            yaml_path='models.testing',
            effective=True,
            kind='config'
        )

        assert claim_specific > claim_general

    def test_effective_beats_ineffective(self, dbt_project):
        """Effective project configs should beat ineffective ones."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claim_effective = PropertyClaim(
            source_type='dbt_project.yml',
            source_path=Path('tests/testing/dbt_project.yml'),
            model=model,
            name='materialized',
            value='table',
            yaml_path='models.testing.complex_config',
            effective=True,
            kind='config'
        )

        claim_ineffective = PropertyClaim(
            source_type='dbt_project.yml',
            source_path=Path('tests/testing/dbt_project.yml'),
            model=model,
            name='materialized',
            value='view',
            yaml_path='models.testing.vanilla',  # Wrong path for this model
            effective=False,
            kind='config'
        )

        assert claim_effective > claim_ineffective

    def test_same_model_required(self, dbt_project):
        """Comparing claims from different models should raise exception."""
        model1 = dbt_project.get_model_by_name('c_changed_name')
        model2 = dbt_project.get_model_by_name('v_a')

        claim1 = PropertyClaim(
            source_type='model',
            source_path=model1.file_path_full,
            model=model1,
            name='materialized',
            value='table',
            kind='config'
        )

        claim2 = PropertyClaim(
            source_type='model',
            source_path=model2.file_path_full,
            model=model2,
            name='materialized',
            value='view',
            kind='config'
        )

        with pytest.raises(Exception, match='Models are different'):
            claim1 > claim2

    def test_same_property_name_required(self, dbt_project):
        """Comparing different properties should raise exception."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claim1 = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='materialized',
            value='table',
            kind='config'
        )

        claim2 = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='schema',
            value='public',
            kind='config'
        )

        with pytest.raises(Exception, match='Properties are different'):
            claim1 > claim2


class TestPropertyDiscovery:
    """Test property discovery from various sources."""

    def test_find_schema_files(self, dbt_project):
        """Should find schema.yml files in model directory hierarchy."""
        model = dbt_project.get_model_by_name('c_changed_name')
        schema_files = find_schema_files(
            model.file_path_full,
            dbt_project.root_folder
        )

        # Should find at least the schema.yml in complex_config directory
        assert len(schema_files) > 0
        assert any('schema.yml' in str(f) for f in schema_files)

    def test_collect_project_configs(self, dbt_project):
        """Should collect configs from dbt_project.yml."""
        model = dbt_project.get_model_by_name('c_changed_name')
        claims = collect_project_configs(model)

        # Should find configs from dbt_project.yml
        assert len(claims) > 0

        # All claims should be for the correct model
        assert all(claim.model == model for claim in claims)
        assert all(claim.source_type == 'dbt_project.yml' for claim in claims)
        assert all(claim.kind == 'config' for claim in claims)

        # Check for specific expected configs
        config_names = {claim.name for claim in claims}
        assert 'materialized' in config_names  # Root level config

    def test_collect_schema_properties(self, dbt_project):
        """Should collect properties from schema.yml."""
        model = dbt_project.get_model_by_name('c_changed_name')
        schema_file = Path('tests/testing/complex_config/stg/schema.yml')

        claims = collect_schema_properties(schema_file, model)

        # Should find properties for c_changed_name
        assert len(claims) > 0

        # All claims should be for the correct model
        assert all(claim.model == model for claim in claims)
        assert all(claim.source_type == 'schema.yml' for claim in claims)

        # Check for specific properties
        property_names = {claim.name for claim in claims}
        assert 'description' in property_names
        assert 'columns' in property_names
        assert 'materialized' in property_names  # From config block

    def test_collect_sql_configs(self, dbt_project):
        """Should collect configs from model SQL files."""
        # The c_changed_name model has a config() call for name
        model = dbt_project.get_model_by_name('c_changed_name')
        claims = collect_sql_configs(model)

        # Should find the name config
        assert len(claims) > 0
        assert any(claim.name == 'name' for claim in claims)

        # All claims should be from model source
        assert all(claim.source_type == 'model' for claim in claims)
        assert all(claim.kind == 'config' for claim in claims)

    def test_collect_all_model_claims(self, dbt_project):
        """Should collect claims from all sources."""
        model = dbt_project.get_model_by_name('c_changed_name')
        claims = collect_model_claims(model)

        # Should have claims from multiple sources
        source_types = {claim.source_type for claim in claims}

        # We expect at least project and schema claims
        # (model has a config for name)
        assert 'dbt_project.yml' in source_types
        assert 'schema.yml' in source_types
        assert 'model' in source_types

    def test_collect_claims_vanilla_model(self, dbt_project):
        """Should collect claims for vanilla models."""
        model = dbt_project.get_model_by_name('v_a')
        claims = collect_model_claims(model)

        # Should have claims from project and schema
        source_types = {claim.source_type for claim in claims}
        assert 'dbt_project.yml' in source_types
        assert 'schema.yml' in source_types

        # Check for specific properties
        property_names = {claim.name for claim in claims}
        assert 'materialized' in property_names


class TestPropertyResolution:
    """Test property precedence resolution."""

    def test_resolve_precedence_model_wins(self, dbt_project):
        """Model-level config should win in resolution."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claims = [
            PropertyClaim(
                source_type='dbt_project.yml',
                source_path=Path('tests/testing/dbt_project.yml'),
                model=model,
                name='materialized',
                value='view',
                yaml_path='models.testing',
                effective=True,
                kind='config'
            ),
            PropertyClaim(
                source_type='schema.yml',
                source_path=Path('tests/testing/complex_config/schema.yml'),
                model=model,
                name='materialized',
                value='table',
                kind='config'
            ),
            PropertyClaim(
                source_type='model',
                source_path=model.file_path_full,
                model=model,
                name='materialized',
                value='ephemeral',
                kind='config'
            ),
        ]

        resolved = resolve_property_precedence(claims)

        assert 'materialized' in resolved
        assert resolved['materialized'].source_type == 'model'
        assert resolved['materialized'].value == 'ephemeral'

    def test_resolve_precedence_schema_wins(self, dbt_project):
        """schema.yml should win over dbt_project.yml."""
        model = dbt_project.get_model_by_name('v_a')

        claims = [
            PropertyClaim(
                source_type='dbt_project.yml',
                source_path=Path('tests/testing/dbt_project.yml'),
                model=model,
                name='materialized',
                value='view',
                yaml_path='models.testing',
                effective=True,
                kind='config'
            ),
            PropertyClaim(
                source_type='schema.yml',
                source_path=Path('tests/testing/vanilla/stg/schema.yml'),
                model=model,
                name='materialized',
                value='ephemeral',
                kind='config'
            ),
        ]

        resolved = resolve_property_precedence(claims)

        assert 'materialized' in resolved
        assert resolved['materialized'].source_type == 'schema.yml'
        assert resolved['materialized'].value == 'ephemeral'

    def test_resolve_multiple_properties(self, dbt_project):
        """Should resolve multiple different properties."""
        model = dbt_project.get_model_by_name('c_changed_name')

        claims = collect_model_claims(model)
        resolved = resolve_property_precedence(claims)

        # Should have resolved multiple properties
        assert len(resolved) > 0

        # Each property should have exactly one winning claim
        for prop_name, claim in resolved.items():
            assert isinstance(claim, PropertyClaim)
            assert claim.name == prop_name

    def test_resolve_empty_claims(self):
        """Should handle empty claims list."""
        resolved = resolve_property_precedence([])
        assert resolved == {}


class TestIntegration:
    """Integration tests for the complete property system."""

    def test_full_property_resolution_flow(self, dbt_project):
        """Test the complete flow from discovery to resolution."""
        model = dbt_project.get_model_by_name('c_changed_name')

        # Collect all claims
        claims = collect_model_claims(model)

        # Verify we got claims from all expected sources
        source_types = {claim.source_type for claim in claims}
        assert len(source_types) >= 2  # At least 2 of the 3 sources

        # Resolve precedence
        resolved = resolve_property_precedence(claims)

        # Should have resolved properties
        assert len(resolved) > 0

        # Verify structure
        for prop_name, claim in resolved.items():
            assert isinstance(claim, PropertyClaim)
            assert claim.name == prop_name
            assert claim.model == model

    def test_property_discovery_for_all_models(self, dbt_project):
        """Verify property discovery works for all models in project."""
        for model in dbt_project.models:
            # Should not raise any exceptions
            claims = collect_model_claims(model)

            # All claims should be for the correct model
            for claim in claims:
                assert claim.model == model

            # Should be able to resolve without errors
            resolved = resolve_property_precedence(claims)
            assert isinstance(resolved, dict)
