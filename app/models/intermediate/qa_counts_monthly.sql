with daily_counts as (
    select * from {{ ref("qa_counts_daily") }}
),

month_key_added as (
    select
        date_trunc('month', date_id) as month_id,
        (date_trunc('month', date_id) + interval '1 month - 1 day')::date as month_end_date,
        t.*,
        to_char(date_id, 'YYYYMM') || '_' || t.comment_id as monthly_comment_id,
        to_char(date_id, 'YYYYMM')
        || '_'
        || t.incident_id as monthly_incident_id
    from
        daily_counts as t
),

first_and_last_flag_added as (
    select
        t.*,
        case
            when
                lag(monthly_incident_id)
                    over (order by monthly_comment_id, date_id)
                = monthly_incident_id
                then false
            else true
        end as is_monthly_first,
        case
            when
                lead(monthly_incident_id)
                    over (order by monthly_comment_id, date_id)
                = monthly_incident_id
                then false
            else true
        end as is_monthly_last
    from month_key_added as t
),

monthly_data_added as (
    select
        month_id,
        monthly_incident_id,
        max(
            case when is_monthly_last then comment_id else null end
        ) as comment_id,
        max(
            case when is_monthly_last then incident_id else null end
        ) as incident_id,
        max(
            case when is_monthly_last then comment_seq else null end
        ) as comment_seq,
        max(
            case when is_monthly_last then comment_div else null end
        ) as comment_div,
        max(
            case when is_monthly_last then comment_by else null end
        ) as comment_by,
        max(
            case when is_monthly_last then comment_date else null end
        ) as comment_date,
        max(case when is_monthly_last then ball_on else null end) as ball_on,
        sum(elapsed_days) as elapsed_days,
        sum(elapsed_days_on_dev) as elapsed_days_on_dev,
        sum(elapsed_days_on_field) as elapsed_days_on_field,
        sum(elapsed_days_on_unknown) as elapsed_days_on_unknown,
        sum(
            case when
                    date_id = least(month_end_date, current_date)
                    and close_count = 0
                    then 1
                else 0
            end
        ) as month_end_active_count,
        sum(
            case when
                    date_id = least(month_end_date, current_date)
                    and close_count = 0
                    and ball_on = 'dev'
                    then 1
                else 0
            end
        ) as month_end_active_count_dev,
        sum(
            case when
                    date_id = least(month_end_date, current_date)
                    and close_count = 0
                    and ball_on = 'field'
                    then 1
                else 0
            end
        ) as month_end_active_count_field,
        sum(
            case when
                    date_id = least(month_end_date, current_date)
                    and close_count = 0
                    and ball_on = 'unknown'
                    then 1
                else 0
            end
        ) as month_end_active_count_unknown,
        sum(comment_count) as comment_count,
        sum(registered_count) as registered_count,
        sum(patch_planned_count) as patch_planned_count,
        sum(close_count) as close_count,
        sum(close_count_normal) as close_count_normal,
        sum(close_count_force) as close_count_force,
        sum(force_close_notice_count) as force_close_notice_count
    from
        first_and_last_flag_added
    group by
        month_id,
        monthly_incident_id
)

select * from monthly_data_added
