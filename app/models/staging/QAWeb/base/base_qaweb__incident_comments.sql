{{ config(
    materialized='view'
) }}

{% set column_settings = [
    ["incident_id", "text"],
    ["comment_seq", "int"],    
    ["comment_div", "text"],
    ["comment_by", "text"],
    ["comment_date", "date"],
    ["comment", "text"]
] %}

with raw_data as (
    select * from {{ ref('seed_qaweb__incident_comments') }}
),

data_type_adjusted as (
    select
        {{ adjust_data_type(column_settings) }}
    from
        raw_data
)

select * from data_type_adjusted
