"""Stale model detection based on file modification times."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import DbtModel
    from .project import DbtProject


@dataclass
class StalenessInfo:
    is_stale: bool
    stale_parents: list[str]
    model_mtime: float
    latest_parent_mtime: float | None


def check_staleness(project: 'DbtProject', model: 'DbtModel') -> StalenessInfo:
    """Check if a model is stale relative to its parents."""
    try:
        model_mtime = model.file_path_full.stat().st_mtime
    except OSError:
        return StalenessInfo(is_stale=False, stale_parents=[], model_mtime=0, latest_parent_mtime=None)

    stale_parents = []
    latest_parent_mtime = None

    for parent in project.graph.predecessors(model):
        if not hasattr(parent, 'file_path_full'):
            continue
        try:
            parent_mtime = parent.file_path_full.stat().st_mtime
            if latest_parent_mtime is None or parent_mtime > latest_parent_mtime:
                latest_parent_mtime = parent_mtime
            if parent_mtime > model_mtime:
                stale_parents.append(parent.name)
        except (OSError, AttributeError):
            continue

    return StalenessInfo(
        is_stale=len(stale_parents) > 0,
        stale_parents=stale_parents,
        model_mtime=model_mtime,
        latest_parent_mtime=latest_parent_mtime,
    )
