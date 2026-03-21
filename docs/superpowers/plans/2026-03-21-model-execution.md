# Model Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run `dbt run`, `dbt test`, and `dbt build` for the current model from within the TUI, showing live streaming output and final status.

**Architecture:** New `RunPanel` widget inside `ModelView` that executes dbt via `asyncio.create_subprocess_exec`, streams stdout/stderr line-by-line into a scrolling `RichLog` widget. Run state (idle/running/passed/failed) is tracked reactively. The dbt project directory is derived from `model.file_path_full`.

**Tech Stack:** `asyncio.create_subprocess_exec`, Textual `RichLog`, `Button`, `reactive`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/backend/runner.py` | Create | `DbtRunner` — async subprocess wrapper |
| `src/dbt_tui/frontend/model_view/run_panel.py` | Create | `RunPanel` widget |
| `src/dbt_tui/frontend/model_view/model_view.py` | Modify | Add `RunPanel` to layout; bind `R`/`T`/`B` |
| `tests/test_runner.py` | Create | Tests for `DbtRunner` |

---

### Task 1: DbtRunner async subprocess wrapper

**Files:**
- Create: `src/dbt_tui/backend/runner.py`
- Test: `tests/test_runner.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_runner.py`:
```python
import pytest
import asyncio
from pathlib import Path
from dbt_tui.backend.runner import DbtRunner, RunResult

@pytest.fixture
def project_path():
    return Path('tests/testing')

@pytest.mark.asyncio
async def test_runner_returns_run_result(project_path):
    runner = DbtRunner(project_path)
    lines = []
    result = await runner.run('run', select='v_a', on_line=lines.append)
    assert isinstance(result, RunResult)

@pytest.mark.asyncio
async def test_runner_populates_lines(project_path):
    runner = DbtRunner(project_path)
    lines = []
    await runner.run('run', select='v_a', on_line=lines.append)
    assert len(lines) > 0

@pytest.mark.asyncio
async def test_runner_returncode_in_result(project_path):
    runner = DbtRunner(project_path)
    result = await runner.run('run', select='v_a')
    assert hasattr(result, 'returncode')
    assert isinstance(result.returncode, int)

@pytest.mark.asyncio
async def test_runner_failed_command_nonzero(project_path):
    runner = DbtRunner(project_path)
    result = await runner.run('run', select='nonexistent_model_xyz_123')
    # dbt exits non-zero if no models matched
    assert result.returncode != 0 or result.lines  # either error or output

@pytest.mark.asyncio
async def test_runner_cancel(project_path):
    """Cancelling the runner task should not raise unhandled exceptions."""
    runner = DbtRunner(project_path)
    task = asyncio.create_task(runner.run('run', select='v_a'))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_runner.py -x --tb=short -q
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `DbtRunner`**

Create `src/dbt_tui/backend/runner.py`:
```python
"""Async dbt subprocess runner."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Awaitable


@dataclass
class RunResult:
    command: str
    select: str
    returncode: int
    lines: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.returncode == 0


class DbtRunner:
    """Runs dbt commands as async subprocesses."""

    def __init__(self, project_path: Path | str):
        self.project_path = Path(project_path)

    async def run(
        self,
        command: str,
        select: str = '',
        on_line: Callable[[str], None] | None = None,
    ) -> RunResult:
        """
        Run `dbt <command> --select <select>` in project_path.
        Calls on_line(line) for each stdout/stderr line as it arrives.
        """
        cmd = ['dbt', command, '--no-use-colors']
        if select:
            cmd += ['--select', select]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.project_path,
        )

        lines: list[str] = []
        assert proc.stdout is not None

        async for raw in proc.stdout:
            line = raw.decode('utf-8', errors='replace').rstrip()
            lines.append(line)
            if on_line:
                on_line(line)

        await proc.wait()
        return RunResult(
            command=command,
            select=select,
            returncode=proc.returncode or 0,
            lines=lines,
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_runner.py -x --tb=short -q
```

Note: tests require dbt to be installed and the test project to be valid. If dbt not available, tests will show non-zero return code which is still a valid `RunResult`. Mark with `@pytest.mark.integration` if needed and skip in CI without dbt.

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/backend/runner.py tests/test_runner.py
git commit -m "feat: add DbtRunner async subprocess wrapper"
```

---

### Task 2: RunPanel widget

**Files:**
- Create: `src/dbt_tui/frontend/model_view/run_panel.py`
- Test: `tests/test_model_view.py`

- [ ] **Step 1: Write failing test**

In `tests/test_model_view.py`:
```python
@pytest.mark.asyncio
async def test_run_panel_has_buttons():
    app = DbtTuiFrontend()
    async with app.run_test() as pilot:
        # Navigate to model view with a model set
        ...
        panel = app.screen.query_one('RunPanel')
        assert panel.query_one('#btn-run') is not None
        assert panel.query_one('#btn-test') is not None
        assert panel.query_one('#btn-build') is not None
```

- [ ] **Step 2: Implement `RunPanel`**

Create `src/dbt_tui/frontend/model_view/run_panel.py`:
```python
"""Run panel for executing dbt commands on the current model."""
from __future__ import annotations
import asyncio
from textual.app import ComposeResult
from textual.widgets import Button, RichLog, Static
from textual.containers import Vertical, Horizontal
from textual.widget import Widget
from textual import work
from rich.text import Text

from dbt_tui.backend.runner import DbtRunner


class RunPanel(Widget):
    DEFAULT_CSS = """
    RunPanel {
        height: 12;
        border: solid $primary;
    }
    RunPanel #run-controls {
        height: 3;
    }
    RunPanel #run-log {
        height: 9;
    }
    RunPanel Button {
        min-width: 10;
    }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Run', id='btn-run', variant='success'),
            Button('Test', id='btn-test', variant='primary'),
            Button('Build', id='btn-build', variant='warning'),
            Button('Cancel', id='btn-cancel', variant='error', disabled=True),
            Static('', id='run-status'),
            id='run-controls',
        )
        yield RichLog(id='run-log', wrap=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case 'btn-run':
                self._start_run('run')
            case 'btn-test':
                self._start_run('test')
            case 'btn-build':
                self._start_run('build')
            case 'btn-cancel':
                self._cancel()

    def _start_run(self, command: str) -> None:
        model = self.app.model
        project = self.app.project
        if model is None or project is None:
            return
        self._set_running(True)
        log = self.query_one('#run-log', RichLog)
        log.clear()
        log.write(Text(f'► dbt {command} --select {model.name}', style='bold'))
        self._run_task = self._execute(command, model.name, project.root_folder)

    @work(exclusive=True, thread=False)
    async def _execute(self, command: str, select: str, project_path) -> None:
        log = self.query_one('#run-log', RichLog)
        status = self.query_one('#run-status', Static)

        runner = DbtRunner(project_path)
        try:
            result = await runner.run(
                command,
                select=select,
                on_line=lambda line: log.write(line),
            )
            if result.success:
                status.update('[green]✓ Passed[/green]')
            else:
                status.update('[red]✗ Failed[/red]')
        except asyncio.CancelledError:
            status.update('[yellow]Cancelled[/yellow]')
        finally:
            self._set_running(False)

    def _cancel(self) -> None:
        # Textual @work handles cancellation
        self.workers.cancel_all()

    def _set_running(self, running: bool) -> None:
        for btn_id in ('#btn-run', '#btn-test', '#btn-build'):
            self.query_one(btn_id, Button).disabled = running
        self.query_one('#btn-cancel', Button).disabled = not running
        if running:
            self.query_one('#run-status', Static).update('[yellow]Running...[/yellow]')
```

- [ ] **Step 3: Add RunPanel to ModelView**

In `frontend/model_view/model_view.py`, add to `compose()`:
```python
from dbt_tui.frontend.model_view.run_panel import RunPanel

# In compose(), add to the Vertical containing model content:
yield RunPanel(id='run-panel')
```

Add bindings:
```python
Binding('r', 'run_model', 'Run'),
Binding('t', 'test_model', 'Test'),
```

Add actions:
```python
def action_run_model(self) -> None:
    self.query_one('#run-panel', RunPanel)._start_run('run')

def action_test_model(self) -> None:
    self.query_one('#run-panel', RunPanel)._start_run('test')
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/frontend/model_view/run_panel.py src/dbt_tui/frontend/model_view/model_view.py
git commit -m "feat: add RunPanel with dbt run/test/build to model view"
```
