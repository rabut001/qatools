{% macro get_adjusted_data(model_name) %}
    {%- set adjust_table_before = "adjust__" + model_name + "__before" -%}
    {%- set adjust_table_after = "adjust__" + model_name + "__after" -%}

    {%- set model = ref(model_name) -%}
    {%- set model_config = get_config_from_model_name(model_name) -%}
    {%- set unique_key = model_config.unique_key -%}

    {%- if unique_key is not string -%} {# checking if unique_key is list or scalar #}
        {%- set keys = unique_key -%}
    {%- else %}
        {%- set keys = [unique_key] -%}
    {%- endif %}

    select * from {{ ref(model_name) }} as t1
    where
        not exists (
            select 1 from {{ ref(adjust_table_before) }} t2
            where
                {% for key in keys -%}
                    t2.{{ key }} = t1.{{ key }}{{ '' if loop.last else ' and ' }}
                {%- endfor %}
        )
    union all
    select * from {{ ref(adjust_table_after) }} t3
{% endmacro %}