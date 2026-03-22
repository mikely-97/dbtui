"""Async dbt subprocess runner."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


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
        cmd = ['dbt', command, '--no-use-colors']
        if select:
            cmd += ['--select', select]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_path,
            )
        except FileNotFoundError:
            # dbt not installed
            line = 'Error: dbt command not found. Is dbt installed?'
            if on_line:
                on_line(line)
            return RunResult(command=command, select=select, returncode=1, lines=[line])

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
