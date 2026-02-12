"""
Structured error tracking for dbt-tui.

This module provides a way to collect, categorize, and expose errors
that occur during project loading and property discovery. Errors are
tracked rather than silently swallowed, allowing the UI to display
warnings to users.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entity import DbtEntityAbstract


class ErrorSeverity(Enum):
    """Severity level for load errors."""
    WARNING = "warning"
    ERROR = "error"


class ErrorCategory(Enum):
    """Category of error for filtering and display."""
    PARSE_ERROR = "parse_error"          # YAML/SQL parsing failed
    FILE_NOT_FOUND = "file_not_found"    # Expected file missing
    INVALID_CONFIG = "invalid_config"    # Invalid configuration
    REF_NOT_FOUND = "ref_not_found"      # Referenced model not found
    PERMISSION_ERROR = "permission"      # File permission issues
    UNKNOWN = "unknown"                  # Uncategorized errors


@dataclass
class LoadError:
    """
    A structured error that occurred during loading.

    Attributes:
        severity: How severe the error is (warning or error)
        category: The type of error
        message: Human-readable error description
        source_path: Path to the file where error occurred
        entity_name: Name of entity affected (if applicable)
        exception: The original exception (if any)
    """
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    source_path: Path | None = None
    entity_name: str | None = None
    exception: Exception | None = None

    def __str__(self) -> str:
        parts = [f"[{self.severity.value.upper()}]"]
        if self.entity_name:
            parts.append(f"({self.entity_name})")
        parts.append(self.message)
        if self.source_path:
            parts.append(f"in {self.source_path}")
        return " ".join(parts)


@dataclass
class ErrorCollector:
    """
    Collects and manages errors during project loading.

    Usage:
        collector = ErrorCollector()
        collector.add_warning("Something went wrong", source_path=some_path)

        # Later, check for errors
        if collector.has_errors:
            for error in collector.errors:
                print(error)
    """
    errors: list[LoadError] = field(default_factory=list)

    def add(
        self,
        severity: ErrorSeverity,
        category: ErrorCategory,
        message: str,
        source_path: Path | None = None,
        entity_name: str | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Add an error to the collection."""
        self.errors.append(LoadError(
            severity=severity,
            category=category,
            message=message,
            source_path=source_path,
            entity_name=entity_name,
            exception=exception,
        ))

    def add_warning(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        source_path: Path | None = None,
        entity_name: str | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Convenience method to add a warning."""
        self.add(
            ErrorSeverity.WARNING,
            category,
            message,
            source_path,
            entity_name,
            exception,
        )

    def add_error(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        source_path: Path | None = None,
        entity_name: str | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Convenience method to add an error."""
        self.add(
            ErrorSeverity.ERROR,
            category,
            message,
            source_path,
            entity_name,
            exception,
        )

    def add_parse_error(
        self,
        message: str,
        source_path: Path,
        exception: Exception | None = None,
    ) -> None:
        """Convenience method to add a parse error."""
        self.add_warning(
            message,
            ErrorCategory.PARSE_ERROR,
            source_path,
            exception=exception,
        )

    def add_ref_not_found(
        self,
        model_name: str,
        ref_name: str,
    ) -> None:
        """Convenience method to add a ref not found warning."""
        self.add_warning(
            f"Model '{model_name}' references '{ref_name}' which was not found",
            ErrorCategory.REF_NOT_FOUND,
            entity_name=model_name,
        )

    @property
    def has_errors(self) -> bool:
        """Check if any errors (not just warnings) exist."""
        return any(e.severity == ErrorSeverity.ERROR for e in self.errors)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings exist."""
        return any(e.severity == ErrorSeverity.WARNING for e in self.errors)

    @property
    def has_any(self) -> bool:
        """Check if any errors or warnings exist."""
        return len(self.errors) > 0

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)

    @property
    def error_count(self) -> int:
        """Count of errors."""
        return sum(1 for e in self.errors if e.severity == ErrorSeverity.ERROR)

    def get_by_severity(self, severity: ErrorSeverity) -> list[LoadError]:
        """Get errors filtered by severity."""
        return [e for e in self.errors if e.severity == severity]

    def get_by_category(self, category: ErrorCategory) -> list[LoadError]:
        """Get errors filtered by category."""
        return [e for e in self.errors if e.category == category]

    def get_for_entity(self, entity_name: str) -> list[LoadError]:
        """Get errors for a specific entity."""
        return [e for e in self.errors if e.entity_name == entity_name]

    def clear(self) -> None:
        """Clear all collected errors."""
        self.errors.clear()

    def merge(self, other: 'ErrorCollector') -> None:
        """Merge errors from another collector into this one."""
        self.errors.extend(other.errors)

    def summary(self) -> str:
        """Get a summary of collected errors."""
        if not self.has_any:
            return "No errors"
        parts = []
        if self.error_count > 0:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count > 0:
            parts.append(f"{self.warning_count} warning(s)")
        return ", ".join(parts)
