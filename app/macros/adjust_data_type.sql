{% macro adjust_data_type(column_settings) %} 
    {% for column_setting in column_settings %}
        {% if column_setting[1] == 'date' %}
            try_cast_date(cast({{ column_setting[0] }} as text)) as {{ column_setting[0] }}{{ '' if loop.last else ',' }}
        {% else %}
            cast({{ column_setting[0] }} as {{ column_setting[1] }}) as {{ column_setting[0] }}{{ '' if loop.last else ',' }}
        {% endif %}
    {% endfor %}
{% endmacro %}