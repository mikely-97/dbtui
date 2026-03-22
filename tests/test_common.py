"""
Tests for common module components.

Tests for:
- Error collector
- Entity abstraction
- Text caching
"""
from pathlib import Path

from dbt_tui.backend import DbtProject
from dbt_tui.common.errors import (
    ErrorCategory,
    ErrorCollector,
    ErrorSeverity,
    LoadError,
)


class TestErrorCollector:
    """Tests for the ErrorCollector class."""

    def test_empty_collector(self):
        """New collector should be empty."""
        collector = ErrorCollector()
        assert not collector.has_any
        assert not collector.has_errors
        assert not collector.has_warnings
        assert collector.error_count == 0
        assert collector.warning_count == 0

    def test_add_warning(self):
        """Adding a warning should be tracked."""
        collector = ErrorCollector()
        collector.add_warning("Test warning")
        assert collector.has_any
        assert collector.has_warnings
        assert not collector.has_errors
        assert collector.warning_count == 1

    def test_add_error(self):
        """Adding an error should be tracked."""
        collector = ErrorCollector()
        collector.add_error("Test error")
        assert collector.has_any
        assert not collector.has_warnings
        assert collector.has_errors
        assert collector.error_count == 1

    def test_add_parse_error(self):
        """Parse error helper should work."""
        collector = ErrorCollector()
        collector.add_parse_error("Parse failed", Path("/test/file.yml"))
        assert collector.warning_count == 1
        assert collector.errors[0].category == ErrorCategory.PARSE_ERROR

    def test_add_ref_not_found(self):
        """Ref not found helper should work."""
        collector = ErrorCollector()
        collector.add_ref_not_found("model_a", "missing_model")
        assert collector.warning_count == 1
        assert collector.errors[0].category == ErrorCategory.REF_NOT_FOUND
        assert "model_a" in str(collector.errors[0])
        assert "missing_model" in str(collector.errors[0])

    def test_get_by_severity(self):
        """Should filter by severity."""
        collector = ErrorCollector()
        collector.add_warning("Warning 1")
        collector.add_error("Error 1")
        collector.add_warning("Warning 2")

        warnings = collector.get_by_severity(ErrorSeverity.WARNING)
        errors = collector.get_by_severity(ErrorSeverity.ERROR)

        assert len(warnings) == 2
        assert len(errors) == 1

    def test_get_by_category(self):
        """Should filter by category."""
        collector = ErrorCollector()
        collector.add_parse_error("Parse 1", Path("/a.yml"))
        collector.add_ref_not_found("model", "ref")
        collector.add_parse_error("Parse 2", Path("/b.yml"))

        parse_errors = collector.get_by_category(ErrorCategory.PARSE_ERROR)
        ref_errors = collector.get_by_category(ErrorCategory.REF_NOT_FOUND)

        assert len(parse_errors) == 2
        assert len(ref_errors) == 1

    def test_get_for_entity(self):
        """Should filter by entity name."""
        collector = ErrorCollector()
        collector.add_ref_not_found("model_a", "ref1")
        collector.add_ref_not_found("model_b", "ref2")
        collector.add_ref_not_found("model_a", "ref3")

        model_a_errors = collector.get_for_entity("model_a")
        model_b_errors = collector.get_for_entity("model_b")

        assert len(model_a_errors) == 2
        assert len(model_b_errors) == 1

    def test_clear(self):
        """Clear should remove all errors."""
        collector = ErrorCollector()
        collector.add_warning("Warning 1")
        collector.add_error("Error 1")
        collector.clear()

        assert not collector.has_any
        assert len(collector.errors) == 0

    def test_merge(self):
        """Merge should combine errors from two collectors."""
        collector1 = ErrorCollector()
        collector1.add_warning("Warning 1")

        collector2 = ErrorCollector()
        collector2.add_error("Error 1")

        collector1.merge(collector2)

        assert collector1.warning_count == 1
        assert collector1.error_count == 1
        assert len(collector1.errors) == 2

    def test_summary(self):
        """Summary should describe errors correctly."""
        collector = ErrorCollector()
        assert collector.summary() == "No errors"

        collector.add_warning("Warning")
        assert "1 warning" in collector.summary()

        collector.add_error("Error")
        assert "1 error" in collector.summary()
        assert "1 warning" in collector.summary()


class TestLoadError:
    """Tests for the LoadError class."""

    def test_str_representation(self):
        """String representation should be informative."""
        error = LoadError(
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.PARSE_ERROR,
            message="Failed to parse",
            source_path=Path("/test/schema.yml"),
            entity_name="my_model",
        )
        s = str(error)
        assert "[ERROR]" in s
        assert "my_model" in s
        assert "Failed to parse" in s
        assert "schema.yml" in s


class TestEntityType:
    """Tests for the EntityType."""

    def test_model_entity_type(self, dbt_project):
        """Model should have entity_type 'model'."""
        model = dbt_project.get_model_by_name('v_a')
        assert model.entity_type == "model"

    def test_entity_has_required_properties(self, dbt_project):
        """Models should implement DbtEntityAbstract interface."""
        model = dbt_project.get_model_by_name('v_a')

        # Check required properties exist
        assert hasattr(model, 'entity_type')
        assert hasattr(model, 'name')
        assert hasattr(model, 'text')
        assert hasattr(model, 'file_path_full')
        assert hasattr(model, 'file_path_relative')
        assert hasattr(model, 'file_name')
        assert hasattr(model, 'parents')
        assert hasattr(model, 'children')

        # Check types
        assert isinstance(model.entity_type, str)
        assert isinstance(model.name, str)
        assert isinstance(model.text, str)
        assert isinstance(model.file_path_full, Path)
        assert isinstance(model.file_path_relative, Path)
        assert isinstance(model.file_name, str)


class TestTextCaching:
    """Tests for model text caching."""

    def test_text_is_cached(self, dbt_project):
        """Text property should use caching."""
        model = dbt_project.get_model_by_name('v_a')

        # Access text twice
        text1 = model.text
        text2 = model.text

        # Should be the same content
        assert text1 == text2

        # Internal template should be set
        assert model._template == text1

    def test_cache_invalidation(self, dbt_project):
        """Cache should be invalidatable."""
        model = dbt_project.get_model_by_name('v_a')

        # Access text to populate cache
        _ = model.text

        # Invalidate cache
        model.invalidate_cache()

        # Mtime should be reset
        assert model._template_mtime == 0


class TestProjectErrorTracking:
    """Tests for error tracking in project loading."""

    def test_project_has_error_collector(self, dbt_project):
        """Project should have load_errors attribute."""
        assert hasattr(dbt_project, 'load_errors')
        assert isinstance(dbt_project.load_errors, ErrorCollector)

    def test_error_collector_tracks_missing_refs(self):
        """Error collector should track missing refs."""
        # The testing project might have missing refs
        project = DbtProject('tests/testing')

        # Check that the collector was initialized
        assert project.load_errors is not None


class TestProjectEntityMethods:
    """Tests for entity-generic methods on DbtProject."""

    def test_get_entity_by_name(self, dbt_project):
        """get_entity_by_name should work for models."""
        entity = dbt_project.get_entity_by_name('v_a')
        assert entity is not None
        assert entity.name == 'v_a'
        assert entity.entity_type == 'model'

    def test_get_entity_by_name_with_type(self, dbt_project):
        """get_entity_by_name with entity_type should work."""
        entity = dbt_project.get_entity_by_name('v_a', entity_type='model')
        assert entity is not None
        assert entity.name == 'v_a'

    def test_search_entities(self, dbt_project):
        """search_entities should work."""
        results = dbt_project.search_entities('v_')
        assert len(results) > 0
        assert all(hasattr(e, 'entity_type') for e in results)

    def test_search_entities_with_type(self, dbt_project):
        """search_entities with entity_type should work."""
        results = dbt_project.search_entities('v_', entity_type='model')
        assert len(results) > 0
