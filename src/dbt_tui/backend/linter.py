"""SQL linting — uses sqlfluff if available, falls back to sqlglot."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LintIssue:
    line: int
    col: int
    code: str
    message: str
    severity: str = 'warning'  # warning | error


def lint_sql(sql: str, dialect: str = 'duckdb') -> list[LintIssue]:
    """Lint SQL and return issues. Uses sqlfluff if installed, else sqlglot."""
    # Try sqlfluff first
    try:
        return _lint_with_sqlfluff(sql, dialect)
    except ImportError:
        pass

    # Fall back to sqlglot parse check
    return _lint_with_sqlglot(sql, dialect)


def _lint_with_sqlfluff(sql: str, dialect: str) -> list[LintIssue]:
    """Lint using sqlfluff."""
    import sqlfluff
    result = sqlfluff.lint(sql, dialect=dialect)
    issues = []
    for violation in result:
        issues.append(LintIssue(
            line=violation.get('start_line_no', 0),
            col=violation.get('start_line_pos', 0),
            code=violation.get('code', ''),
            message=violation.get('description', ''),
            severity='error' if violation.get('code', '').startswith('PRS') else 'warning',
        ))
    return issues


def _lint_with_sqlglot(sql: str, dialect: str) -> list[LintIssue]:
    """Basic linting using sqlglot parse errors."""
    issues = []
    try:
        import sqlglot
        import sqlglot.errors
    except ImportError:
        return issues

    # Strip Jinja first
    import re
    clean = re.sub(r'\{\{[^}]+\}\}', 'placeholder', sql)
    clean = re.sub(r'\{%-?\s*.*?-?%\}', '', clean, flags=re.DOTALL)

    try:
        stmts = sqlglot.parse(clean, dialect=dialect)
        for stmt in stmts:
            if stmt is None:
                continue
            # Check for SELECT * (common lint rule)
            import sqlglot.expressions as exp
            for star in stmt.find_all(exp.Star):
                issues.append(LintIssue(
                    line=0, col=0, code='L044',
                    message='SELECT * used — consider explicit column list',
                    severity='warning',
                ))
                break  # Only report once
    except sqlglot.errors.ParseError as e:
        issues.append(LintIssue(
            line=0, col=0, code='PRS',
            message=f'SQL parse error: {e}',
            severity='error',
        ))

    return issues
