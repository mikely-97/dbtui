# Git Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show git status (modified/staged/untracked), git log (last N commits), and git blame for the current model file, in a new `GitPanel` within the model view.

**Architecture:** New `backend/git.py` with `GitInfo` dataclass collected via `asyncio.create_subprocess_exec(['git', ...])`. `GitPanel` widget in model view shows a tabbed view: Status tab (file status), Log tab (recent commits), Blame tab (annotated SQL). No git library dependency — just shell calls.

**Tech Stack:** `asyncio.create_subprocess_exec`, Textual `DataTable`/`RichLog`/`TabbedContent`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/dbt_tui/backend/git.py` | Create | `GitInfo`, `get_git_status`, `get_git_log`, `get_git_blame` |
| `src/dbt_tui/frontend/model_view/git_panel.py` | Create | `GitPanel` widget |
| `src/dbt_tui/frontend/model_view/model_view.py` | Modify | Add Git tab to TabbedContent |
| `tests/test_git.py` | Create | Tests for git backend functions |

---

### Task 1: Git backend

**Files:**
- Create: `src/dbt_tui/backend/git.py`
- Test: `tests/test_git.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_git.py`:
```python
import pytest
import asyncio
from pathlib import Path
from dbt_tui.backend.git import get_git_status, get_git_log, get_git_blame, GitFileStatus

@pytest.fixture
def model_path():
    # Use a real file in a git repo
    return Path('tests/testing/vanilla/stg/v_a.sql')

@pytest.mark.asyncio
async def test_get_git_status_returns_status(model_path):
    status = await get_git_status(model_path)
    assert isinstance(status, GitFileStatus)

@pytest.mark.asyncio
async def test_git_status_has_state_field(model_path):
    status = await get_git_status(model_path)
    # state is one of: 'untracked', 'modified', 'staged', 'clean', 'unknown'
    assert status.state in ('untracked', 'modified', 'staged', 'clean', 'unknown')

@pytest.mark.asyncio
async def test_get_git_log_returns_list(model_path):
    log = await get_git_log(model_path, n=5)
    assert isinstance(log, list)

@pytest.mark.asyncio
async def test_get_git_log_entries_have_fields(model_path):
    log = await get_git_log(model_path, n=5)
    if log:  # may be empty if no commits touch this file
        entry = log[0]
        assert hasattr(entry, 'hash')
        assert hasattr(entry, 'author')
        assert hasattr(entry, 'message')

@pytest.mark.asyncio
async def test_get_git_blame_returns_lines(model_path):
    lines = await get_git_blame(model_path)
    assert isinstance(lines, list)

@pytest.mark.asyncio
async def test_not_in_repo_returns_gracefully(tmp_path):
    """File outside a git repo should return unknown/empty gracefully."""
    f = tmp_path / 'test.sql'
    f.write_text('select 1')
    status = await get_git_status(f)
    assert status.state == 'unknown'
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_git.py -x --tb=short -q
```

- [ ] **Step 3: Implement git backend**

Create `src/dbt_tui/backend/git.py`:
```python
"""Git integration — status, log, blame via subprocess."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitFileStatus:
    state: str  # 'clean' | 'modified' | 'staged' | 'untracked' | 'unknown'
    xy: str = ''  # raw two-char git status code


@dataclass
class GitLogEntry:
    hash: str
    author: str
    date: str
    message: str


@dataclass
class GitBlameLine:
    hash: str
    author: str
    line_no: int
    content: str


async def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run a command, return (returncode, stdout)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        return proc.returncode or 0, stdout.decode('utf-8', errors='replace')
    except FileNotFoundError:
        return 1, ''
    except Exception:
        return 1, ''


async def get_git_status(file_path: Path) -> GitFileStatus:
    """Return git status for a single file."""
    rc, out = await _run(
        ['git', 'status', '--porcelain', str(file_path)],
        cwd=file_path.parent,
    )
    if rc != 0:
        return GitFileStatus(state='unknown')
    line = out.strip()
    if not line:
        return GitFileStatus(state='clean')
    xy = line[:2]
    if xy == '??':
        return GitFileStatus(state='untracked', xy=xy)
    if xy[0] != ' ':
        return GitFileStatus(state='staged', xy=xy)
    return GitFileStatus(state='modified', xy=xy)


async def get_git_log(file_path: Path, n: int = 10) -> list[GitLogEntry]:
    """Return last n git log entries for a file."""
    rc, out = await _run(
        ['git', 'log', f'-{n}', '--pretty=format:%h|%an|%ad|%s', '--date=short',
         '--', str(file_path)],
        cwd=file_path.parent,
    )
    if rc != 0 or not out.strip():
        return []
    entries = []
    for line in out.strip().splitlines():
        parts = line.split('|', 3)
        if len(parts) == 4:
            entries.append(GitLogEntry(*parts))
    return entries


async def get_git_blame(file_path: Path) -> list[GitBlameLine]:
    """Return git blame for a file."""
    rc, out = await _run(
        ['git', 'blame', '--porcelain', str(file_path)],
        cwd=file_path.parent,
    )
    if rc != 0 or not out.strip():
        # Fall back: return lines without blame
        try:
            text = file_path.read_text()
            return [
                GitBlameLine(hash='', author='', line_no=i + 1, content=line)
                for i, line in enumerate(text.splitlines())
            ]
        except Exception:
            return []

    # Parse porcelain blame format
    lines: list[GitBlameLine] = []
    current_hash = ''
    current_author = ''
    line_no = 0
    for raw in out.splitlines():
        if raw.startswith('\t'):
            lines.append(GitBlameLine(
                hash=current_hash[:7],
                author=current_author,
                line_no=line_no,
                content=raw[1:],
            ))
        elif raw.startswith('author '):
            current_author = raw[7:]
        elif len(raw) == 40 or (len(raw.split()) >= 3 and len(raw.split()[0]) == 40):
            parts = raw.split()
            current_hash = parts[0]
            line_no = int(parts[2]) if len(parts) >= 3 else 0
    return lines
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_git.py -x --tb=short -q
```

- [ ] **Step 5: Commit**

```bash
git add src/dbt_tui/backend/git.py tests/test_git.py
git commit -m "feat: add git backend (status, log, blame)"
```

---

### Task 2: GitPanel widget

**Files:**
- Create: `src/dbt_tui/frontend/model_view/git_panel.py`
- Modify: `src/dbt_tui/frontend/model_view/model_view.py`

- [ ] **Step 1: Create GitPanel**

`src/dbt_tui/frontend/model_view/git_panel.py`:
```python
"""Git information panel."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import DataTable, RichLog, TabbedContent, TabPane, Static
from textual.widget import Widget
from textual import work

from dbt_tui.backend.git import get_git_status, get_git_log, get_git_blame


_STATUS_ICONS = {
    'clean': '✓ clean',
    'modified': '✎ modified',
    'staged': '● staged',
    'untracked': '? untracked',
    'unknown': '– (not in git)',
}


class GitPanel(Widget):
    DEFAULT_CSS = """
    GitPanel { border: solid $warning; height: 1fr; }
    """

    def compose(self) -> ComposeResult:
        yield Static('', id='git-status-bar')
        with TabbedContent():
            with TabPane('Log'):
                yield DataTable(id='git-log-table')
            with TabPane('Blame'):
                yield RichLog(id='git-blame-log', wrap=False)

    def on_mount(self) -> None:
        log_table = self.query_one('#git-log-table', DataTable)
        log_table.add_columns('Hash', 'Author', 'Date', 'Message')

    def refresh_model(self, model) -> None:
        if model is None:
            return
        self._load_git_info(model.file_path_full)

    @work(exclusive=True)
    async def _load_git_info(self, file_path) -> None:
        status = await get_git_status(file_path)
        log_entries = await get_git_log(file_path, n=15)
        blame_lines = await get_git_blame(file_path)

        # Update status bar
        label = _STATUS_ICONS.get(status.state, status.state)
        self.query_one('#git-status-bar', Static).update(f'git: {label}')

        # Update log table
        table = self.query_one('#git-log-table', DataTable)
        table.clear()
        for e in log_entries:
            table.add_row(e.hash, e.author, e.date, e.message)

        # Update blame
        blame_log = self.query_one('#git-blame-log', RichLog)
        blame_log.clear()
        for bl in blame_lines:
            prefix = f'[dim]{bl.hash:7} {bl.author[:12]:12}[/dim] '
            blame_log.write(prefix + bl.content)
```

- [ ] **Step 2: Add Git tab to ModelView**

In `frontend/model_view/model_view.py`, inside the `TabbedContent` (added in docs plan):
```python
from dbt_tui.frontend.model_view.git_panel import GitPanel

# In TabbedContent:
with TabPane('Git', id='tab-git'):
    yield GitPanel(id='git-panel')
```

In `on_model_change`:
```python
self.query_one('#git-panel', GitPanel).refresh_model(model)
```

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Step 4: Commit**

```bash
git add src/dbt_tui/frontend/model_view/git_panel.py \
        src/dbt_tui/frontend/model_view/model_view.py
git commit -m "feat: add git panel (log, blame, status) to model view"
```
