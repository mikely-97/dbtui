"""
Tests for property writing functionality.

These tests verify that:
1. SchemaYmlWriter can read, modify, and save schema.yml files
2. SqlConfigWriter can modify config() calls in model SQL
3. Helper functions correctly find or create schema paths
"""

from pathlib import Path

import yaml

from dbt_tui.backend.property_writer import (
    SchemaYmlWriter,
    SqlConfigWriter,
    WriteResult,
    find_or_create_schema_path,
    write_property_to_model_sql,
    write_property_to_schema,
)


class TestSchemaYmlWriter:
    """Test SchemaYmlWriter class."""

    def test_load_existing_file(self, temp_schema_file):
        """Should load and parse existing schema.yml."""
        writer = SchemaYmlWriter(temp_schema_file)
        data = writer.load()

        assert data['version'] == 2
        assert len(data['models']) == 1
        assert data['models'][0]['name'] == 'existing_model'

    def test_load_nonexistent_creates_default(self, tmp_path):
        """Should create default structure for new files."""
        schema_path = tmp_path / 'new_schema.yml'
        writer = SchemaYmlWriter(schema_path)
        data = writer.load()

        assert data['version'] == 2
        assert data['models'] == []

    def test_get_or_create_model_entry_existing(self, temp_schema_file):
        """Should find existing model entry."""
        writer = SchemaYmlWriter(temp_schema_file)
        entry = writer.get_or_create_model_entry('existing_model')

        assert entry['name'] == 'existing_model'
        assert entry['description'] == 'Test model'

    def test_get_or_create_model_entry_new(self, temp_schema_file):
        """Should create new model entry if not exists."""
        writer = SchemaYmlWriter(temp_schema_file)
        entry = writer.get_or_create_model_entry('new_model')

        assert entry['name'] == 'new_model'
        assert len(writer._data['models']) == 2

    def test_set_config_property(self, temp_schema_file):
        """Should set config property correctly."""
        writer = SchemaYmlWriter(temp_schema_file)
        writer.set_property('existing_model', 'materialized', 'table', 'config')
        writer.save()

        # Reload and verify
        data = yaml.safe_load(temp_schema_file.read_text())
        assert data is not None
        assert data['models'][0]['config']['materialized'] == 'table'

    def test_set_regular_property(self, temp_schema_file):
        """Should set regular property correctly."""
        writer = SchemaYmlWriter(temp_schema_file)
        writer.set_property('existing_model', 'docs', {'show': True}, 'property')
        writer.save()

        # Reload and verify
        data = yaml.safe_load(temp_schema_file.read_text())
        assert data is not None
        assert data['models'][0]['docs'] == {'show': True}

    def test_save_preserves_other_content(self, temp_schema_file):
        """Save should not lose other models/properties."""
        writer = SchemaYmlWriter(temp_schema_file)
        writer.set_property('new_model', 'tags', ['test'], 'property')
        writer.save()

        # Reload and verify original model still exists
        data = yaml.safe_load(temp_schema_file.read_text())
        assert data is not None
        model_names = [m['name'] for m in data['models']]
        assert 'existing_model' in model_names
        assert 'new_model' in model_names

    def test_remove_config_property(self, temp_schema_file):
        """Should remove config property."""
        writer = SchemaYmlWriter(temp_schema_file)
        writer.set_property('existing_model', 'materialized', 'table', 'config')
        writer.save()

        # Now remove it
        writer2 = SchemaYmlWriter(temp_schema_file)
        result = writer2.remove_property('existing_model', 'materialized', 'config')
        writer2.save()

        assert result is True
        data = yaml.safe_load(temp_schema_file.read_text())
        assert data is not None
        assert 'config' not in data['models'][0]

    def test_remove_regular_property(self, temp_schema_file):
        """Should remove regular property."""
        writer = SchemaYmlWriter(temp_schema_file)
        result = writer.remove_property('existing_model', 'description', 'property')
        writer.save()

        assert result is True
        data = yaml.safe_load(temp_schema_file.read_text())
        assert data is not None
        assert 'description' not in data['models'][0]


class TestSqlConfigWriter:
    """Test SqlConfigWriter class."""

    def test_load_file(self, temp_sql_file):
        """Should load SQL file content."""
        writer = SqlConfigWriter(temp_sql_file)
        content = writer.load()

        assert 'SELECT * FROM source_table' in content

    def test_has_config_false(self, temp_sql_file):
        """Should return False when no config exists."""
        writer = SqlConfigWriter(temp_sql_file)

        assert writer.has_config() is False

    def test_has_config_true(self, temp_sql_file_with_config):
        """Should return True when config exists."""
        writer = SqlConfigWriter(temp_sql_file_with_config)

        assert writer.has_config() is True

    def test_add_new_config(self, temp_sql_file):
        """Should add config at top of file."""
        writer = SqlConfigWriter(temp_sql_file)
        writer.set_config_value('materialized', 'table')
        writer.save()

        content = temp_sql_file.read_text()
        assert "{{ config(materialized='table') }}" in content
        assert content.startswith('{{ config')

    def test_modify_existing_config(self, temp_sql_file_with_config):
        """Should modify existing config value."""
        writer = SqlConfigWriter(temp_sql_file_with_config)
        writer.set_config_value('materialized', 'table')
        writer.save()

        content = temp_sql_file_with_config.read_text()
        assert "materialized='table'" in content
        assert "materialized='view'" not in content

    def test_add_to_existing_config(self, temp_sql_file_with_config):
        """Should add new key to existing config."""
        writer = SqlConfigWriter(temp_sql_file_with_config)
        writer.set_config_value('unique_key', 'id')
        writer.save()

        content = temp_sql_file_with_config.read_text()
        assert "unique_key='id'" in content
        assert "materialized='view'" in content

    def test_format_string_value(self, temp_sql_file):
        """Should format string values with quotes."""
        writer = SqlConfigWriter(temp_sql_file)
        writer.set_config_value('schema', 'staging')
        writer.save()

        content = temp_sql_file.read_text()
        assert "schema='staging'" in content

    def test_format_bool_value(self, temp_sql_file):
        """Should format boolean values correctly."""
        writer = SqlConfigWriter(temp_sql_file)
        writer.set_config_value('enabled', True)
        writer.save()

        content = temp_sql_file.read_text()
        assert "enabled=true" in content

    def test_format_list_value(self, temp_sql_file):
        """Should format list values correctly."""
        writer = SqlConfigWriter(temp_sql_file)
        writer.set_config_value('tags', ['staging', 'important'])
        writer.save()

        content = temp_sql_file.read_text()
        assert "tags=['staging', 'important']" in content


class TestFindOrCreateSchemaPath:
    """Test schema path finding logic."""

    def test_finds_schema_in_model_dir(self, dbt_project):
        """Should find schema.yml in model's directory."""
        model = dbt_project.get_model_by_name('c_changed_name')
        path = find_or_create_schema_path(model)

        assert path.exists()
        assert path.name == 'schema.yml'

    def test_returns_new_path_when_none_exists(self, dbt_project):
        """Should return path for new schema.yml when none found."""
        # Use a model in a directory without schema.yml (mart has no schema.yml)
        model = dbt_project.get_model_by_name('v_d')
        path = find_or_create_schema_path(model)

        # Should return a path (either existing in parent or new in model's directory)
        assert path.name in ('schema.yml', '_schema.yml', 'models.yml', '_models.yml')


class TestWritePropertyToSchema:
    """Test high-level schema writing function."""

    def test_write_to_existing_schema(self, dbt_project, tmp_path):
        """Should write property to existing schema file."""
        # Create a temporary schema file
        schema_path = tmp_path / 'schema.yml'
        schema_path.write_text(yaml.dump({'version': 2, 'models': []}))

        model = dbt_project.get_model_by_name('v_a')
        result = write_property_to_schema(
            model, 'materialized', 'table', 'config', schema_path
        )

        assert result.success is True
        assert 'materialized' in result.message

        data = yaml.safe_load(schema_path.read_text())
        assert data is not None
        assert data['models'][0]['name'] == model.name
        assert data['models'][0]['config']['materialized'] == 'table'

    def test_write_returns_error_on_failure(self, dbt_project, tmp_path):
        """Should return error result on failure."""
        # Create a read-only directory scenario (simulate failure)
        model = dbt_project.get_model_by_name('v_a')
        invalid_path = tmp_path / 'nonexistent' / 'deep' / 'nested'

        # This should work since we create parents
        result = write_property_to_schema(
            model, 'test', 'value', 'property', invalid_path / 'schema.yml'
        )

        # Should succeed because mkdir creates parents
        assert result.success is True


def test_write_description_and_tags_round_trip(tmp_path, dbt_project):
    """Writing description + tags creates valid schema.yml with both fields."""
    model = dbt_project.models[0]
    schema_path = tmp_path / 'schema.yml'

    from dbt_tui.backend.property_writer import write_property_to_schema
    r1 = write_property_to_schema(model, 'description', 'Test description', 'property', schema_path)
    assert r1.success

    r2 = write_property_to_schema(model, 'tags', ['finance', 'core'], 'config', schema_path)
    assert r2.success

    import yaml
    data = yaml.safe_load(schema_path.read_text())
    assert data is not None
    model_entry = next(m for m in data['models'] if m['name'] == model.name)
    assert model_entry['description'] == 'Test description'
    assert model_entry['config']['tags'] == ['finance', 'core']


class TestWritePropertyToModelSql:
    """Test high-level SQL writing function."""

    def test_write_config_to_model(self, dbt_project):
        """Should write config to model SQL (integration test)."""
        model = dbt_project.get_model_by_name('v_a')
        original_content = model.file_path_full.read_text()

        try:
            result = write_property_to_model_sql(model, 'test_property', 'test_value')

            assert result.success is True
            content = model.file_path_full.read_text()
            assert "test_property='test_value'" in content
        finally:
            # Restore original content
            model.file_path_full.write_text(original_content)


class TestWriteResult:
    """Test WriteResult dataclass."""

    def test_success_result(self):
        """Should create success result."""
        result = WriteResult(True, "Success message", Path('/test/path'))

        assert result.success is True
        assert result.message == "Success message"
        assert result.file_path == Path('/test/path')

    def test_failure_result(self):
        """Should create failure result."""
        result = WriteResult(False, "Error message")

        assert result.success is False
        assert result.message == "Error message"
        assert result.file_path is None
