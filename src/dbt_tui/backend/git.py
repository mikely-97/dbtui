"""Git integration — status, log, blame via subprocess."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitFileStatus:
    state: str  # 'clean' | 'modified' | 'staged' | 'untracked' | 'unknown'
    xy: str = ''


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
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        return proc.returncode or 0, stdout.decode('utf-8', errors='replace')
    except (FileNotFoundError, OSError):
        return 1, ''


async def get_git_status(file_path: Path) -> GitFileStatus:
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
    rc, out = await _run(
        ['git', 'blame', '--porcelain', str(file_path)],
        cwd=file_path.parent,
    )
    if rc != 0 or not out.strip():
        try:
            text = file_path.read_text()
            return [
                GitBlameLine(hash='', author='', line_no=i + 1, content=line)
                for i, line in enumerate(text.splitlines())
            ]
        except Exception:
            return []

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
        elif len(raw.split()) >= 3 and len(raw.split()[0]) == 40:
            parts = raw.split()
            current_hash = parts[0]
            line_no = int(parts[2]) if len(parts) >= 3 else 0
    return lines
