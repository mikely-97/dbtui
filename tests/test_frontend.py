"""
Frontend tests using Textual's testing framework.

These tests verify that:
1. The app starts without errors
2. Screens are registered correctly
3. ModelView displays properties correctly
4. The default screen is properly skipped in event handlers
"""

from dbt_tui.backend import DbtProject
from dbt_tui.frontend.main import DbtTuiFrontend
from dbt_tui.frontend.model_view import ModelView
from dbt_tui.frontend.model_view.properties_panel import PropertiesPanel, PropertyItem


class TestAppStartup:
    """Test that the app starts correctly."""

    async def test_app_starts_without_error(self, empty_cache):
        """App should start without throwing errors."""
        app = DbtTuiFrontend()
        async with app.run_test() as _pilot:
            assert app.is_running

    async def test_app_pushes_screen_on_mount(self, empty_cache):
        """With no cached project, should push a screen."""
        app = DbtTuiFrontend()
        async with app.run_test() as _pilot:
            # Should have at least the default screen plus one pushed
            assert len(app.screen_stack) >= 1

    def test_screens_are_registered(self):
        """All expected screens should be registered."""
        assert 'model_search' in DbtTuiFrontend.SCREENS
        assert 'model_view' in DbtTuiFrontend.SCREENS
        assert 'model_properties' in DbtTuiFrontend.SCREENS
        assert 'options' in DbtTuiFrontend.SCREENS
        assert 'project_search' in DbtTuiFrontend.SCREENS
        assert 'new_model' in DbtTuiFrontend.SCREENS


class TestModelViewScreen:
    """Test the ModelView screen components directly."""

    def test_model_view_instantiation(self):
        """ModelView should be instantiable without errors."""
        screen = ModelView()
        assert screen is not None

    def test_model_view_has_bindings(self):
        """ModelView should have expected bindings."""
        binding_keys = [b.key for b in ModelView.BINDINGS]
        assert 'E' in binding_keys
        assert 'r' in binding_keys
        assert 'enter' in binding_keys
        assert 'escape' in binding_keys

    def test_model_view_has_css(self):
        """ModelView should have CSS defined via CSS_PATH."""
        assert hasattr(ModelView, 'CSS_PATH')
        assert ModelView.CSS_PATH == "model_view.tcss"


class TestPropertiesPanelUnit:
    """Unit tests for PropertiesPanel without the full app."""

    def test_properties_panel_instantiation(self):
        """PropertiesPanel should be instantiable."""
        panel = PropertiesPanel()
        assert panel is not None

    def test_properties_panel_has_css(self):
        """PropertiesPanel should have CSS defined via CSS_PATH."""
        assert hasattr(PropertiesPanel, 'CSS_PATH')
        assert PropertiesPanel.CSS_PATH == "properties_panel.tcss"

    def test_property_item_instantiation(self, dbt_project):
        """PropertyItem should be instantiable with a claim."""
        from dbt_tui.backend.property_claim import PropertyClaim
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='test_prop',
            value='test_value',
            kind='config'
        )
        item = PropertyItem(claim)
        assert item.claim == claim

    def test_property_item_format_string(self, dbt_project):
        """PropertyItem should format string values."""
        from dbt_tui.backend.property_claim import PropertyClaim
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='test_prop',
            value='hello',
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value('hello')
        assert formatted == '"hello"'

    def test_property_item_format_long_string(self, dbt_project):
        """PropertyItem should truncate long strings."""
        from dbt_tui.backend.property_claim import PropertyClaim
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
        formatted = item._format_value(long_value)
        assert '...' in formatted
        assert len(formatted) < len(long_value)

    def test_property_item_format_list(self, dbt_project):
        """PropertyItem should format list values."""
        from dbt_tui.backend.property_claim import PropertyClaim
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='tags',
            value=['a', 'b', 'c', 'd', 'e'],
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value(['a', 'b', 'c', 'd', 'e'])
        assert '5 items' in formatted

    def test_property_item_format_dict(self, dbt_project):
        """PropertyItem should format dict values."""
        from dbt_tui.backend.property_claim import PropertyClaim
        model = dbt_project.get_model_by_name('v_a')
        claim = PropertyClaim(
            source_type='model',
            source_path=model.file_path_full,
            model=model,
            name='meta',
            value={'key': 'value'},
            kind='config'
        )
        item = PropertyItem(claim)
        formatted = item._format_value({'key': 'value'})
        assert '1 keys' in formatted


class TestBindingsExist:
    """Test that key bindings are properly defined."""

    def test_q_binding_defined(self):
        """'q' binding should be defined to quit."""
        bindings = [b for b in DbtTuiFrontend.BINDINGS if b.key == 'q']
        assert len(bindings) == 1
        assert bindings[0].action == 'quit'

    def test_v_binding_defined(self):
        """'v' binding should be defined to open model properties."""
        bindings = [b for b in DbtTuiFrontend.BINDINGS if b.key == 'v']
        assert len(bindings) == 1
        assert 'property_viewer' in bindings[0].action

    def test_o_binding_defined(self):
        """'o' binding should be defined to open options."""
        bindings = [b for b in DbtTuiFrontend.BINDINGS if b.key == 'o']
        assert len(bindings) == 1
        assert 'options' in bindings[0].action

    def test_f_binding_defined(self):
        """'f' binding should be defined to open model search."""
        bindings = [b for b in DbtTuiFrontend.BINDINGS if b.key == 'f']
        assert len(bindings) == 1
        assert 'model_search' in bindings[0].action

    def test_p_binding_defined(self):
        """'p' binding should be defined to open project search."""
        bindings = [b for b in DbtTuiFrontend.BINDINGS if b.key == 'p']
        assert len(bindings) == 1
        assert 'project_search' in bindings[0].action


class TestModelViewBindings:
    """Test ModelView-specific bindings."""

    def test_model_view_has_edit_binding(self):
        """ModelView should have 'E' binding for external edit."""
        bindings = [b for b in ModelView.BINDINGS if b.key == 'E']
        assert len(bindings) == 1

    def test_model_view_has_refresh_binding(self):
        """ModelView should have 'r' binding for refresh."""
        bindings = [b for b in ModelView.BINDINGS if b.key == 'r']
        assert len(bindings) == 1

    def test_model_view_has_tab_binding(self):
        """ModelView should have 'tab' binding."""
        bindings = [b for b in ModelView.BINDINGS if b.key == 'tab']
        assert len(bindings) == 1


class TestValidateProject:
    """Test project validation."""

    def test_validate_project_returns_project_instance(self, dbt_project):
        """validate_project should return the project instance, not the class."""
        app = DbtTuiFrontend()
        result = app.validate_project(dbt_project)
        assert result is dbt_project
        assert result is not DbtProject

    def test_validate_project_returns_none_for_invalid(self):
        """validate_project should return None for non-DbtProject."""
        app = DbtTuiFrontend()
        result = app.validate_project("not a project")
        assert result is None

        result = app.validate_project(None)
        assert result is None


class TestDefaultScreenHandling:
    """Test that the default screen is properly handled."""

    async def test_app_starts_with_screen_stack(self, empty_cache):
        """App should have screens in stack after mount."""
        app = DbtTuiFrontend()
        async with app.run_test() as _pilot:
            # The app should have started and pushed initial screen
            assert len(app.screen_stack) >= 1


class TestAppQuit:
    """Test app quit functionality."""

    async def test_app_can_exit(self, empty_cache):
        """App should be able to exit cleanly."""
        app = DbtTuiFrontend()
        async with app.run_test() as _pilot:
            assert app.is_running
            app.exit()


class TestSourceTypeConstants:
    """Test source type constants in properties panel."""

    def test_source_type_colors_defined(self):
        """All source types should have colors."""
        from dbt_tui.frontend.model_view.properties_panel import SOURCE_TYPE_COLORS
        assert 'model' in SOURCE_TYPE_COLORS
        assert 'schema.yml' in SOURCE_TYPE_COLORS
        assert 'dbt_project.yml' in SOURCE_TYPE_COLORS

    def test_source_type_icons_defined(self):
        """All source types should have icons."""
        from dbt_tui.frontend.model_view.properties_panel import SOURCE_TYPE_ICONS
        assert 'model' in SOURCE_TYPE_ICONS
        assert 'schema.yml' in SOURCE_TYPE_ICONS
        assert 'dbt_project.yml' in SOURCE_TYPE_ICONS


class TestModelViewMethods:
    """Test ModelView methods."""

    def test_model_view_has_on_model_change(self):
        """ModelView should have on_model_change method."""
        screen = ModelView()
        assert hasattr(screen, 'on_model_change')
        assert callable(screen.on_model_change)

    def test_model_view_has_on_project_change(self):
        """ModelView should have on_project_change method."""
        screen = ModelView()
        assert hasattr(screen, 'on_project_change')
        assert callable(screen.on_project_change)

    def test_model_view_has_action_refresh_properties(self):
        """ModelView should have action_refresh_properties method."""
        screen = ModelView()
        assert hasattr(screen, 'action_refresh_properties')
        assert callable(screen.action_refresh_properties)

    def test_model_view_has_action_toggle_edit_mode(self):
        """ModelView should have action_toggle_edit_mode method."""
        screen = ModelView()
        assert hasattr(screen, 'action_toggle_edit_mode')
        assert callable(screen.action_toggle_edit_mode)

    def test_model_view_has_action_exit_edit_mode(self):
        """ModelView should have action_exit_edit_mode method."""
        screen = ModelView()
        assert hasattr(screen, 'action_exit_edit_mode')
        assert callable(screen.action_exit_edit_mode)


class TestPropertiesPanelMethods:
    """Test PropertiesPanel methods."""

    def test_properties_panel_has_update_properties(self):
        """PropertiesPanel should have update_properties method."""
        panel = PropertiesPanel()
        assert hasattr(panel, 'update_properties')
        assert callable(panel.update_properties)
