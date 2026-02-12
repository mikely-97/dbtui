"""
dbt-tui - Terminal UI for dbt projects

Usage:
    python -m dbt_tui [project_dir] [--log-level LEVEL]
    python -m dbt_tui --logs-dir
    python -m dbt_tui --version

If project_dir is not specified, launches with the last opened project.
"""
import argparse
import sys
from importlib.metadata import version as get_version, PackageNotFoundError
from pathlib import Path

from .frontend import frontend as DbtTuiFrontend
from .common import load_cache, save_cache, get_logs_dir, setup_logging, parse_log_level


def get_app_version() -> str:
    """Get the application version from package metadata."""
    try:
        return get_version("dbt-tui")
    except PackageNotFoundError:
        return "0.0.0-dev"


def main():
    parser = argparse.ArgumentParser(
        prog='dbt-tui',
        description='Terminal UI for exploring and managing dbt projects'
    )
    parser.add_argument(
        'project_dir',
        nargs='?',
        default=None,
        help='Path to dbt project directory (optional, uses last project if not specified)'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'%(prog)s {get_app_version()}',
        help='Show version number and exit'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='WARNING',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: WARNING). INFO includes speed metrics.'
    )
    parser.add_argument(
        '--logs-dir',
        action='store_true',
        help='Print the logs directory path and exit'
    )

    args = parser.parse_args()

    # Handle --logs-dir: print path and exit
    if args.logs_dir:
        print(get_logs_dir())
        sys.exit(0)

    # Setup logging with specified level
    log_level = parse_log_level(args.log_level)
    setup_logging(log_level)

    # If project_dir is provided, validate it and save to cache
    if args.project_dir:
        project_path = Path(args.project_dir).resolve()

        if not project_path.exists():
            print(f"Error: Directory not found: {project_path}", file=sys.stderr)
            sys.exit(1)

        if not (project_path / 'dbt_project.yml').exists():
            print(f"Error: Not a dbt project (no dbt_project.yml found): {project_path}", file=sys.stderr)
            sys.exit(1)

        # Load existing cache to preserve external_editor_command
        existing_cache = load_cache()

        # Save the project path to cache so the app loads it
        save_cache(
            project_path=project_path,
            model_name=None,
            external_editor_command=existing_cache.external_editor_command
        )

    # Launch the app
    app = DbtTuiFrontend()
    app.run()


if __name__ == '__main__':
    main()
