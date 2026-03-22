"""
Centralized logging configuration for dbt-tui.

Logs are stored in the same directory as the cache (platformdirs user cache).
Logging level can be configured via CLI --log-level argument.

Log levels and what they contain:
    DEBUG: Detailed execution info, internal state, timing for each operation
    INFO: Speed metrics, major operations (project load, model changes, file writes)
    WARNING: Non-critical issues (missing refs, parse failures, config conflicts)
    ERROR: Critical failures that prevent operations
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from platformdirs import user_cache_dir

# Global state for logging configuration
_logging_configured = False
_log_level = logging.WARNING  # Default level


def get_logs_dir() -> Path:
    """
    Get the directory where logs are stored.

    Returns the same directory as the cache: ~/.cache/dbt-tui/ (Linux),
    ~/Library/Caches/dbt-tui/ (macOS), or %APPDATA%/dbt-tui/Cache/ (Windows).
    """
    logs_dir = Path(user_cache_dir("dbt-tui")) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_current_log_file() -> Path:
    """Get the path to the current session's log file."""
    logs_dir = get_logs_dir()
    # Use date-based log file
    date_str = datetime.now().strftime("%Y-%m-%d")
    return logs_dir / f"dbt-tui-{date_str}.log"


def setup_logging(level: int = logging.WARNING) -> None:
    """
    Configure logging for the entire application.

    Args:
        level: Logging level (logging.DEBUG, INFO, WARNING, ERROR)

    Logs are written to:
        1. A file in the logs directory (always)
        2. stderr if level is DEBUG (for development)

    Call this once at application startup.
    """
    global _logging_configured, _log_level

    if _logging_configured:
        return

    _log_level = level

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Get root logger for dbt_tui
    root_logger = logging.getLogger('dbt_tui')
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # File handler - always write to log file
    log_file = get_current_log_file()
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # File gets everything
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler - only for DEBUG level
    if level <= logging.DEBUG:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Also configure the root logger for any stray logging calls
    logging.getLogger().setLevel(logging.WARNING)

    _logging_configured = True

    # Log startup
    logger = get_logger('startup')
    logger.info(f"Logging initialized at {level_name(level)} level")
    logger.debug(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (will be prefixed with 'dbt_tui.')

    Returns:
        A configured logger instance

    Example:
        logger = get_logger('backend.project')
        logger.info("Project loaded successfully")
    """
    return logging.getLogger(f'dbt_tui.{name}')


def level_name(level: int) -> str:
    """Convert logging level int to name string."""
    return logging.getLevelName(level)


def parse_log_level(level_str: str) -> int:
    """
    Parse a log level string to logging constant.

    Args:
        level_str: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR' (case-insensitive)

    Returns:
        The corresponding logging.* constant

    Raises:
        ValueError: If level_str is not a valid level name
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
    }

    upper = level_str.upper()
    if upper not in level_map:
        valid = ', '.join(level_map.keys())
        raise ValueError(f"Invalid log level '{level_str}'. Must be one of: {valid}")

    return level_map[upper]


def is_logging_enabled_for(level: int) -> bool:
    """Check if logging is enabled for the given level."""
    return _log_level <= level


def cleanup_old_logs(keep_days: int = 7) -> int:
    """
    Remove log files older than keep_days.

    Args:
        keep_days: Number of days of logs to keep

    Returns:
        Number of files deleted
    """
    logs_dir = get_logs_dir()
    now = datetime.now()
    deleted = 0

    for log_file in logs_dir.glob("dbt-tui-*.log"):
        # Parse date from filename
        try:
            date_str = log_file.stem.replace("dbt-tui-", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            age_days = (now - file_date).days

            if age_days > keep_days:
                log_file.unlink()
                deleted += 1
        except (ValueError, OSError):
            pass  # Skip files with unexpected names or permission issues

    return deleted
