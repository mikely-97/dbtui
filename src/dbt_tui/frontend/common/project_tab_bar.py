"""Tab bar for switching between open projects."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button


class ProjectTabBar(Widget):
    """Horizontal tab bar showing open projects."""

    DEFAULT_CSS = """
    ProjectTabBar {
        height: 3;
        background: $panel;
        layout: horizontal;
    }
    ProjectTabBar Button {
        min-width: 16;
        height: 3;
    }
    ProjectTabBar Button.-active-tab {
        background: $accent;
        color: $text;
    }
    ProjectTabBar #add-project-btn {
        min-width: 3;
        width: 3;
    }
    """

    class ProjectSelected(Message):
        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class AddProjectRequested(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Horizontal(id='tabs-row')
        yield Button('+', id='add-project-btn', variant='default')

    def refresh_projects(self, projects: list, active_index: int) -> None:
        """Rebuild tab buttons for the given project list."""
        row = self.query_one('#tabs-row', Horizontal)
        for child in list(row.children):
            child.remove()
        for i, project in enumerate(projects):
            name = project.root_folder.name
            btn = Button(name, id=f'project-tab-{i}')
            if i == active_index:
                btn.add_class('-active-tab')
            row.mount(btn)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ''
        if btn_id == 'add-project-btn':
            self.post_message(self.AddProjectRequested())
        elif btn_id.startswith('project-tab-'):
            idx = int(btn_id.split('-')[-1])
            self.post_message(self.ProjectSelected(idx))
