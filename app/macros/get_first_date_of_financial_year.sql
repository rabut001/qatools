{%- macro get_first_date_of_financial_year(years_count) -%} 
    case when
            extract(month from current_date) <= 3
            then make_date((extract(year from current_date))::int - {{years_count}}, 4, 1)
        else make_date((extract(year from current_date))::int - {{years_count}} + 1, 4, 1)
    end
{%- endmacro -%}