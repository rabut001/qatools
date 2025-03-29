with min_registered_date as (
    select min(registered_date) as min_date from {{ ref('stg_qaweb__incidents') }}
),

min_registered_date_detail as (
    select
        min_date,
        extract(year from min_date)::int as min_date_year,
        extract(month from min_date) as min_date_month
    from min_registered_date

),

start_date as (
    select
        case
            when min_date_month <= 3 then make_date(min_date_year - 1, 4, 1)
            else make_date(min_date_year, 4, 1)
        end as start_date
    from
        min_registered_date_detail
),

today_detail as (
    select
        current_date as today_date,
        extract(year from current_date)::int as today_year,
        extract(month from current_date)::int as today_month
),

end_date as (
    select
        case
            when today_month <= 3 then make_date(today_year + 1, 3, 31)
            else make_date(today_year + 2, 3, 31)
        end as end_date
    from today_detail
),

base_table as (
    select
        generate_series(
            start_date.start_date, end_date.end_date, '1 day'
        )::date as date_id
    from
        start_date, end_date
),

calendar_table as (
    select
        date_id,
        extract(year from date_id) as year,
        extract(month from date_id) as month,
        extract(day from date_id) as day,
        extract(year from (date_id - interval '3 months')) as financial_year,
        floor(
            1 + (extract(month from (date_id - interval '3 months')) - 1) / 3
        ) as financial_quater,
        case
            when to_char(date_id, 'Dy') = 'Sun' then '日'
            when to_char(date_id, 'Dy') = 'Mon' then '月'
            when to_char(date_id, 'Dy') = 'Tue' then '火'
            when to_char(date_id, 'Dy') = 'Wed' then '水'
            when to_char(date_id, 'Dy') = 'Thu' then '木'
            when to_char(date_id, 'Dy') = 'Fri' then '金'
            when to_char(date_id, 'Dy') = 'Sat' then '土'
        end as day_of_week_jp
    from
        base_table
)

select * from calendar_table
