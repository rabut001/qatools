{{ config(
    materialized='view'
) }}

{% set column_settings = [
    ["incident_id", "text"],
    ["title", "text"],
    ["incident_div", "text"],
    ["category", "text"],
    ["category2", "text"],
    ["category3", "text"],
    ["hospital", "text"],
    ["registered_by", "text"],
    ["registered_date", "date"],
    ["impact", "text"],
    ["impact_by_register", "text"],
    ["related_incident", "text"],
    ["description", "text"],
    ["assigned_to", "text"],
    ["solution_div", "text"],
    ["latest_comment_by", "text"],
    ["latest_comment_date", "date"],
    ["first_response_date", "date"],
    ["patch_no", "text"],
    ["close_date", "date"],
    ["status", "text"],
    ["server", "text"],
    ["version", "text"],
    ["version_ehr", "text"],
    ["comment_div", "text"],
    ["last_updated_date", "date"],
    ["approved_date", "date"],
    ["delivery_planned_date", "date"],
    ["comment_history", "text"],
    ["critical", "text"],
    ["event", "text"],
    ["event_date", "date"],
    ["external_case_id", "text"],
    ["additional_item1", "text"],
    ["additional_item2", "text"],
    ["additional_item3", "text"],
    ["additional_item4", "text"]
] %}


with raw_data as (
    select * from {{ ref('seed_qaweb__incidents') }}
),

data_type_adjusted as (
    select
        {{ adjust_data_type(column_settings) }}
    from
        raw_data
)

select * from data_type_adjusted
