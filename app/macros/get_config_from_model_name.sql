{% macro get_config_from_model_name(model_name) %}

{% set model_ref = ref(model_name) %}
{% set model_schema = model_ref.schema %}

{% set ns = namespace(config=none) %}

{% if execute %}
    {% for node in graph.nodes.values() %}
        {%- if node.schema == model_schema and (node.name == model_name or node.alias == model_name) -%}
	        {% set ns.config = node.config %}
        {%- endif -%}
    {% endfor %}
{% endif %}

{{ return(ns.config) }}

{% endmacro %}