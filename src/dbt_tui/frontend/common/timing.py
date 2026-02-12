"""
Timing utilities for frontend performance debugging.

Timing logs are output at INFO level. Use --log-level INFO to see them.
"""

import time
from contextlib import contextmanager
from functools import wraps

from ...common.logging import get_logger

# Get timing logger
timing_logger = get_logger('timing')


@contextmanager
def timed_block(name: str):
    """Context manager to time a block of code and log the result."""
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    timing_logger.info(f"{name}: {elapsed_ms:.1f}ms")


def timed(func):
    """Decorator to time a function and log the result."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        timing_logger.info(f"{func.__qualname__}: {elapsed_ms:.1f}ms")
        return result
    return wrapper


class TimingContext:
    """Accumulates timing for multiple operations."""

    def __init__(self, name: str):
        self.name = name
        self.timings: dict[str, float] = {}

    def record(self, step: str, elapsed_ms: float):
        self.timings[step] = elapsed_ms

    @contextmanager
    def step(self, step_name: str):
        start = time.perf_counter()
        yield
        self.timings[step_name] = (time.perf_counter() - start) * 1000

    def log(self):
        """Log accumulated timing info at INFO level."""
        total = sum(self.timings.values())
        timing_logger.info(f"{self.name} total: {total:.1f}ms")
        for step, ms in self.timings.items():
            timing_logger.info(f"  - {step}: {ms:.1f}ms")
