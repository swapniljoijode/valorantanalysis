{#
    Use the custom schema name verbatim (e.g. "staging", "marts") instead of
    dbt's default of prefixing it with the target schema ("analytics_staging").
    This keeps the warehouse layout clean: raw -> staging -> marts.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
