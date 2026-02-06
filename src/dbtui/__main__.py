"""
dbtui - Terminal UI for dbt projects

Usage:
    python -m dbtui [project_dir]

If project_dir is not specified, launches with the last opened project.
"""
import argparse
import sys
from pathlib import Path

from .frontend import frontend as dbtuiFrontend
from .common import load_cache, save_cache


def main():
    parser = argparse.ArgumentParser(
        prog='dbtui',
        description='Terminal UI for exploring and managing dbt projects'
    )
    parser.add_argument(
        'project_dir',
        nargs='?',
        default=None,
        help='Path to dbt project directory (optional, uses last project if not specified)'
    )

    args = parser.parse_args()

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
    app = dbtuiFrontend()
    app.run()


if __name__ == '__main__':
    main()
