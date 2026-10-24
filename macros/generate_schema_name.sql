{#- Schemas heißen genau so wie konfiguriert (staging, intermediate, …) statt main_staging.
    Gold-Modelle ohne eigenes Schema landen in main – dort, wo man ohne Präfix abfragt. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}{{ target.schema }}{%- else -%}{{ custom_schema_name | trim }}{%- endif -%}
{%- endmacro %}
