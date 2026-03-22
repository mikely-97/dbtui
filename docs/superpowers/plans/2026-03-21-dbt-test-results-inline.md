# dbt Test Results Inline Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Tests" tab to ModelView that runs `dbt test --select <model>` and shows each test's pass/fail status in a DataTable.

**Architecture:** New `TestPanel` widget in `model_view/test_panel.py`. Parses dbt test output lines to extract `PASS`/`FAIL` per test name. Displayed in a `DataTable(test_name, status, message)`. Added as a new TabPane in `model_view.py`. Output parsing is pure Python — no new dependencies.

**Tech Stack:** Textual (`DataTable`, `Button`, `Static`, `@work`), existing `DbtRunner`.

---

### File map
| File | Change |
|------|--------|
| `src/dbt_tui/frontend/model_view/test_panel.py` | Create — TestPanel widget |
| `src/dbt_tui/frontend/model_view/model_view.py` | Add "Tests" tab |
| `tests/test_runner.py` | Add tests for result parsing helper |

---

### Task 1: Result parser helper and unit tests

**Files:**
- Create: `src/dbt_tui/frontend/model_view/test_panel.py` (parser only first)
- Modify: `tests/test_runner.py`

- [ ] **Step 1: Write failing tests for the parser**

Add to `tests/test_runner.py`:

```python
from dbt_tui.frontend.model_view.test_panel import parse_test_results, TestResult


def test_parse_passing_test():
    lines = [
        "Running with dbt=1.8.0",
        "  PASS test_not_null_stg_orders_id .......... [PASS in 0.14s]",
        "Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].name == 'test_not_null_stg_orders_id'
    assert results[0].status == 'PASS'


def test_parse_failing_test():
    lines = [
        "  FAIL 1 test_unique_stg_orders_id ......... [FAIL in 0.08s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].name == 'test_unique_stg_orders_id'
    assert results[0].status == 'FAIL'


def test_parse_warn_test():
    lines = [
        "  WARN 2 test_accepted_values_status ...... [WARN in 0.21s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 1
    assert results[0].status == 'WARN'


def test_parse_empty_output():
    results = parse_test_results([])
    assert results == []


def test_parse_mixed_output():
    lines = [
        "  PASS test_a ......... [PASS in 0.1s]",
        "  FAIL 1 test_b ....... [FAIL in 0.2s]",
        "  PASS test_c ......... [PASS in 0.1s]",
    ]
    results = parse_test_results(lines)
    assert len(results) == 3
    statuses = {r.name: r.status for r in results}
    assert statuses['test_a'] == 'PASS'
    assert statuses['test_b'] == 'FAIL'
    assert statuses['test_c'] == 'PASS'
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_runner.py::test_parse_passing_test -v
```
Expected: FAIL — `ImportError`

- [ ] **Step 3: Create `test_panel.py` with parser + widget**

Create `src/dbt_tui/frontend/model_view/test_panel.py`:

```python
"""Test results panel — runs dbt test and shows per-test pass/fail."""
from __future__ import annotations
import asyncio
import re
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Static
from textual.containers import Horizontal
from textual.widget import Widget
from textual import work

from dbt_tui.backend.runner import DbtRunner


@dataclass
class TestResult:
    name: str
    status: str          # PASS | FAIL | WARN | ERROR
    detail: str = ''


# Matches lines like:
#   PASS test_name ...... [PASS in 0.1s]
#   FAIL 1 test_name .... [FAIL in 0.2s]
#   WARN 3 test_name .... [WARN in 0.3s]
_LINE_RE = re.compile(
    r'^\s+(PASS|FAIL|WARN|ERROR)(?:\s+\d+)?\s+([\w.]+)',
    re.IGNORECASE,
)


def parse_test_results(lines: list[str]) -> list[TestResult]:
    """Parse dbt test stdout lines into structured TestResult objects."""
    results = []
    for line in lines:
        m = _LINE_RE.match(line)
        if m:
            status = m.group(1).upper()
            name = m.group(2)
            results.append(TestResult(name=name, status=status))
    return results


_STATUS_MARKUP = {
    'PASS': '[green]PASS[/green]',
    'FAIL': '[red]FAIL[/red]',
    'WARN': '[yellow]WARN[/yellow]',
    'ERROR': '[red bold]ERROR[/red bold]',
}


class TestPanel(Widget):
    DEFAULT_CSS = """
    TestPanel { height: 1fr; }
    TestPanel #test-controls { height: 3; }
    TestPanel Button { min-width: 14; }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button('Run Tests', id='btn-run-tests', variant='primary'),
            Button('Cancel', id='btn-cancel-tests', variant='error', disabled=True),
            Static('', id='test-status'),
            id='test-controls',
        )
        yield DataTable(id='test-table', zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one('#test-table', DataTable)
        table.add_columns('Test Name', 'Status')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'btn-run-tests':
            self._start_tests()
        elif event.button.id == 'btn-cancel-tests':
            self.workers.cancel_all()

    def _start_tests(self) -> None:
        model = self.app.model  # type: ignore[attr-defined]
        project = self.app.project  # type: ignore[attr-defined]
        if model is None or project is None:
            return
        self._set_running(True)
        table = self.query_one('#test-table', DataTable)
        table.clear()
        self._run_tests(model.name, project.root_folder)

    @work(exclusive=True, thread=False)
    async def _run_tests(self, select: str, project_path) -> None:
        status = self.query_one('#test-status', Static)
        table = self.query_one('#test-table', DataTable)
        runner = DbtRunner(project_path)
        lines: list[str] = []
        try:
            await runner.run(
                'test',
                select=select,
                on_line=lambda line: lines.append(line),
            )
        except asyncio.CancelledError:
            status.update('[yellow]Cancelled[/yellow]')
            return
        finally:
            self._set_running(False)

        results = parse_test_results(lines)
        if not results:
            status.update('[dim]No test results found[/dim]')
            return

        for r in results:
            markup = _STATUS_MARKUP.get(r.status, r.status)
            table.add_row(r.name, markup)

        passed = sum(1 for r in results if r.status == 'PASS')
        failed = sum(1 for r in results if r.status in ('FAIL', 'ERROR'))
        status.update(
            f'[green]{passed} passed[/green]  [red]{failed} failed[/red]'
            if failed else f'[green]All {passed} passed[/green]'
        )

    def _set_running(self, running: bool) -> None:
        self.query_one('#btn-run-tests', Button).disabled = running
        self.query_one('#btn-cancel-tests', Button).disabled = not running
        if running:
            self.query_one('#test-status', Static).update('[yellow]Running tests...[/yellow]')
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_runner.py -v
```
Expected: all pass.

---

### Task 2: Add Tests tab to ModelView

**Files:**
- Modify: `src/dbt_tui/frontend/model_view/model_view.py`

- [ ] **Step 1: Add import and new TabPane**

In `model_view.py`, add import:
```python
from .test_panel import TestPanel
```

In the `compose` method, inside the `with TabbedContent():` block, add a new TabPane after the "Run" tab:
```python
with TabPane("Tests", id="tab-tests"):
    yield TestPanel(id='test-panel')
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/ -q
```
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/dbt_tui/frontend/model_view/test_panel.py \
        src/dbt_tui/frontend/model_view/model_view.py \
        tests/test_runner.py
git commit -m "feat(model-view): add Tests tab with per-test pass/fail results"
```
