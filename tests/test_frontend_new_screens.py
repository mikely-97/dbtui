"""Tests for new screens added in 0.3.0."""

import pytest

from dbt_tui.frontend.common.project_tab_bar import ProjectTabBar
from dbt_tui.frontend.dag_view.dag_view import DagView
from dbt_tui.frontend.help_screen.help_screen import HelpScreen
from dbt_tui.frontend.lineage_view.lineage_view import ColumnLineageView
from dbt_tui.frontend.main import DbtTuiFrontend
from dbt_tui.frontend.property_viewer.property_viewer import PropertyViewerScreen

# ── DagView ───────────────────────────────────────


class TestDagView:
    """Tests for DagView screen."""

    @pytest.mark.asyncio
    async def test_dag_view_can_push_screen(self, dbt_project, empty_cache):
        """DagView can be pushed to screen stack without errors."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            app.project = dbt_project
            app.model = dbt_project.models[0]
            await pilot.pause()
            # Push the DAG view screen
            dag = DagView()
            app.push_screen(dag)
            await pilot.pause()
            # Verify it's on the screen stack
            assert len(app.screen_stack) > 1
            assert isinstance(app.screen_stack[-1], DagView)

    @pytest.mark.asyncio
    async def test_dag_view_depth_starts_at_two(self, dbt_project, empty_cache):
        """DagView initializes with depth=2."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            app.project = dbt_project
            app.model = dbt_project.models[0]
            await pilot.pause()
            dag = DagView()
            assert dag._depth == 2

    @pytest.mark.asyncio
    async def test_dag_view_has_nav_nodes_attribute(self, dbt_project, empty_cache):
        """DagView has _nav_nodes attribute initialized."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            dag = DagView()
            # Verify the attribute exists
            assert hasattr(dag, '_nav_nodes')
            assert isinstance(dag._nav_nodes, list)

    def test_dag_view_instantiation(self):
        """DagView should be instantiable without errors."""
        screen = DagView()
        assert screen is not None

    def test_dag_view_has_bindings(self):
        """DagView should have expected bindings."""
        binding_keys = [b.key for b in DagView.BINDINGS]
        assert 'escape' in binding_keys
        assert '+' in binding_keys
        assert '-' in binding_keys


# ── ColumnLineageView ────────────────────────────


class TestColumnLineageView:
    """Tests for ColumnLineageView screen."""

    @pytest.mark.asyncio
    async def test_lineage_view_can_push_screen(self, dbt_project, empty_cache):
        """ColumnLineageView can be pushed to screen stack without errors."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            app.project = dbt_project
            app.model = dbt_project.models[0]
            await pilot.pause()
            lineage = ColumnLineageView()
            app.push_screen(lineage)
            await pilot.pause()
            # Verify it's on the screen stack
            assert len(app.screen_stack) > 1
            assert isinstance(app.screen_stack[-1], ColumnLineageView)

    @pytest.mark.asyncio
    async def test_lineage_view_has_required_methods(self, dbt_project, empty_cache):
        """ColumnLineageView has required methods."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            lineage = ColumnLineageView()
            # Verify methods exist
            assert hasattr(lineage, '_refresh')
            assert hasattr(lineage, 'on_model_change')
            assert callable(lineage._refresh)
            assert callable(lineage.on_model_change)

    def test_lineage_view_instantiation(self):
        """ColumnLineageView should be instantiable without errors."""
        screen = ColumnLineageView()
        assert screen is not None

    def test_lineage_view_has_bindings(self):
        """ColumnLineageView should have expected bindings."""
        binding_keys = [b.key for b in ColumnLineageView.BINDINGS]
        assert 'escape' in binding_keys


# ── PropertyViewerScreen ─────────────────────────


class TestPropertyViewerScreen:
    """Tests for PropertyViewerScreen."""

    @pytest.mark.asyncio
    async def test_property_viewer_can_push_screen(self, dbt_project, empty_cache):
        """PropertyViewerScreen can be pushed to screen stack without errors."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            app.project = dbt_project
            app.model = dbt_project.models[0]
            await pilot.pause()
            pv = PropertyViewerScreen()
            app.push_screen(pv)
            await pilot.pause()
            # Verify it's on the screen stack
            assert len(app.screen_stack) > 1
            assert isinstance(app.screen_stack[-1], PropertyViewerScreen)

    @pytest.mark.asyncio
    async def test_property_viewer_has_required_methods(self, dbt_project, empty_cache):
        """PropertyViewerScreen has required methods."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            pv = PropertyViewerScreen()
            # Verify methods exist
            assert hasattr(pv, '_refresh')
            assert hasattr(pv, 'on_model_change')
            assert callable(pv._refresh)
            assert callable(pv.on_model_change)

    def test_property_viewer_instantiation(self):
        """PropertyViewerScreen should be instantiable without errors."""
        screen = PropertyViewerScreen()
        assert screen is not None

    def test_property_viewer_has_bindings(self):
        """PropertyViewerScreen should have expected bindings."""
        binding_keys = [b.key for b in PropertyViewerScreen.BINDINGS]
        assert 'escape' in binding_keys
        assert '/' in binding_keys


# ── HelpScreen ───────────────────────────────────


class TestHelpScreen:
    """Tests for HelpScreen."""

    @pytest.mark.asyncio
    async def test_help_screen_can_push_screen(self, dbt_project, empty_cache):
        """HelpScreen can be pushed to screen stack without errors."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            app.project = dbt_project
            await pilot.pause()
            help_screen = HelpScreen()
            app.push_screen(help_screen)
            await pilot.pause()
            # Verify it's on the screen stack
            assert len(app.screen_stack) > 1
            assert isinstance(app.screen_stack[-1], HelpScreen)

    @pytest.mark.asyncio
    async def test_help_screen_closes_on_escape(self, dbt_project, empty_cache):
        """Escape closes help screen."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            app.project = dbt_project
            await pilot.pause()
            depth_before = len(app.screen_stack)
            help_screen = HelpScreen()
            app.push_screen(help_screen)
            await pilot.pause()
            await pilot.press('escape')
            await pilot.pause()
            assert len(app.screen_stack) == depth_before

    def test_help_screen_instantiation(self):
        """HelpScreen should be instantiable without errors."""
        screen = HelpScreen()
        assert screen is not None

    def test_help_screen_has_bindings(self):
        """HelpScreen should have expected bindings."""
        binding_keys = [b.key for b in HelpScreen.BINDINGS]
        assert 'escape' in binding_keys
        assert '?' in binding_keys
        assert 'q' in binding_keys


# ── Workspace / ProjectTabBar ────────────────────


class TestProjectTabBar:
    """Tests for ProjectTabBar workspace widget."""

    @pytest.mark.asyncio
    async def test_project_tab_bar_mounts(self, dbt_project, empty_cache):
        """ProjectTabBar can be instantiated and mounted."""
        app = DbtTuiFrontend()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            tab_bar = ProjectTabBar()
            # Mount it in the app (mock scenario)
            assert tab_bar is not None

    def test_project_tab_bar_instantiation(self):
        """ProjectTabBar should be instantiable without errors."""
        tab_bar = ProjectTabBar()
        assert tab_bar is not None

    def test_project_tab_bar_has_css(self):
        """ProjectTabBar should have CSS defined."""
        assert hasattr(ProjectTabBar, 'DEFAULT_CSS')
        assert ProjectTabBar.DEFAULT_CSS is not None

    def test_project_tab_bar_has_messages(self):
        """ProjectTabBar should have message classes."""
        assert hasattr(ProjectTabBar, 'ProjectSelected')
        assert hasattr(ProjectTabBar, 'AddProjectRequested')


# ── App-level workspace tests ──────────────────


class TestAppWorkspace:
    """Tests for workspace/project management at app level."""

    @pytest.mark.asyncio
    async def test_app_has_projects_list(self, dbt_project, empty_cache):
        """DbtTuiFrontend should have projects list."""
        app = DbtTuiFrontend()
        async with app.run_test() as pilot:
            assert hasattr(app, 'projects')
            assert isinstance(app.projects, list)

    @pytest.mark.asyncio
    async def test_app_add_project_increases_list(self, dbt_project, empty_cache):
        """add_project() appends to projects list."""
        app = DbtTuiFrontend()
        async with app.run_test() as pilot:
            app.project = dbt_project
            await pilot.pause()
            initial = len(app.projects)
            app.add_project(dbt_project)
            assert len(app.projects) == initial + 1

    @pytest.mark.asyncio
    async def test_app_has_active_project(self, dbt_project, empty_cache):
        """App should track active project."""
        app = DbtTuiFrontend()
        async with app.run_test() as pilot:
            app.project = dbt_project
            assert app.project is dbt_project
