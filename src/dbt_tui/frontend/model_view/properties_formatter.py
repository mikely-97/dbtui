"""
Pure formatting functions for property claims display.

Provides functions to format property values for various display contexts
(full details, short summaries, editing, etc.) without any Textual dependencies.
"""
import json
from typing import Any


def format_full_value(value: Any) -> str:
    """Format property value for full display.

    Args:
        value: The property value to format

    Returns:
        A string representation suitable for full detail views
    """
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, (list, dict)):
        return json.dumps(value, indent=2)
    else:
        return str(value)


def format_short_value(value: Any) -> str:
    """Format property value for short display.

    Args:
        value: The property value to format

    Returns:
        A truncated string representation suitable for list/summary views
    """
    if isinstance(value, str):
        if len(value) > 30:
            return f'"{value[:27]}..."'
        return f'"{value}"'
    elif isinstance(value, list):
        return f"[{len(value)} items]"
    elif isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    else:
        return str(value)


def format_item_value(value: Any) -> str:
    """Format property value for list item display.

    Args:
        value: The property value to format

    Returns:
        A formatted string suitable for displaying in a list item
    """
    if isinstance(value, str):
        if len(value) > 40:
            return f'"{value[:37]}..."'
        return f'"{value}"'
    elif isinstance(value, list):
        if len(value) > 3:
            return f"[{len(value)} items]"
        return str(value)
    elif isinstance(value, dict):
        return f"{{...}} ({len(value)} keys)"
    else:
        return str(value)


def format_current_value(value: Any) -> str:
    """Format property value for editing input field.

    Args:
        value: The property value to format

    Returns:
        A string suitable for input field pre-population
    """
    if isinstance(value, str):
        return value
    elif isinstance(value, (list, dict)):
        return json.dumps(value)
    else:
        return str(value)


def parse_value(value_str: str) -> Any:
    """Parse string input to appropriate Python type.

    Attempts to parse in order: bool, int, float, JSON (list/dict), string.

    Args:
        value_str: The string value to parse

    Returns:
        The parsed value (bool, int, float, dict, list, or str)
    """
    # Try bool
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False
    # Try int
    try:
        return int(value_str)
    except ValueError:
        pass
    # Try float
    try:
        return float(value_str)
    except ValueError:
        pass
    # Try JSON (for lists/dicts)
    try:
        parsed = json.loads(value_str)
        if isinstance(parsed, (list, dict)):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    # Default to string
    return value_str
