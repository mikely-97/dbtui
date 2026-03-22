"""SQL formatting using sqlglot."""


def format_sql(sql: str, dialect: str = 'duckdb') -> str:
    """Format SQL using sqlglot's pretty printer.

    Returns the original SQL unchanged if formatting fails (e.g., Jinja syntax).
    """
    try:
        import sqlglot
        # sqlglot.transpile with pretty=True formats the SQL
        results = sqlglot.transpile(sql, read=dialect, write=dialect, pretty=True)
        return results[0] if results else sql
    except Exception:
        return sql
