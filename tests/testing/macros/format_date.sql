{% macro format_date(date_col, fmt='%Y-%m-%d') %}
    date_format({{ date_col }}, '{{ fmt }}')
{% endmacro %}
