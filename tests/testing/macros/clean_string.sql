{% macro clean_string(value) %}
    lower(trim({{ value }}))
{% endmacro %}
