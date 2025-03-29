with raw_data as (
    select
        comment_id,
        incident_id,
        comment_seq,
        comment_div,
        comment_by,
        comment_date,
        case
            when is_final_closer then comment_date else next_comment_date
        end as next_comment_date,
        ball_on,
        is_closer,
        is_final_closer,
        is_approver,
        is_patch_planned,
        is_force_close_announce,
        is_force_close
    from {{ ref("qa_incident_comments") }}
    where not is_after_final_close
),

calendar as (
    select
        date_id
    from {{ ref("calendar") }}
    where date_id <= current_date
),

comment_data_daily as (
    select
        m.date_id,
        t.*,
        to_char(m.date_id, 'YYYYMMDD')
        || '_'
        || t.comment_id as daily_comment_id,
        to_char(m.date_id, 'YYYYMMDD')
        || '_'
        || t.incident_id as daily_incident_id
    from
        calendar as m
    join raw_data as t
        on
            m.date_id >= t.comment_date
            and (
                m.date_id <= t.next_comment_date or t.next_comment_date is null
            )
),

first_and_last_flag_added as (
    select
        *,
        case
            when
                lag(daily_incident_id) over (order by daily_comment_id)
                = daily_incident_id
                then false
            else true
        end as is_daily_first,
        case
            when
                lead(daily_incident_id) over (order by daily_comment_id)
                = daily_incident_id
                then false
            else true
        end as is_daily_last
    from
        comment_data_daily
),

data_for_mart_added as (
    select
        *,
        case
            when date_id <> next_comment_date then 1 else 0
        end as elapsed_days,
        case
            when date_id <> next_comment_date and ball_on = 'dev' then 1 else 0
        end as elapsed_days_on_dev,
        case
            when
                date_id <> next_comment_date and ball_on = 'field'
                then 1
            else 0
        end as elapsed_days_on_field,
        case
            when
                date_id <> next_comment_date and ball_on = 'unknown'
                then 1
            else 0
        end as elapsed_days_on_unknown,
        case when date_id = comment_date then 1 else 0 end as comment_count,
        case
            when date_id = comment_date and comment_seq = 0 then 1 else 0
        end as registered_count,
        case
            when date_id = comment_date and is_patch_planned then 1 else 0
        end as patch_planned_count,
        case
            when date_id = comment_date and is_final_closer then 1 else 0
        end as close_count,
        case
            when
                date_id = comment_date and is_final_closer and not is_force_close
                then 1
            else 0
        end as close_count_normal,
        case
            when date_id = comment_date and is_force_close then 1 else 0
        end as close_count_force,
        case
            when
                date_id = comment_date and is_force_close_announce
                then 1
            else 0
        end as force_close_notice_count
    from
        first_and_last_flag_added
),

final as (
    select
        date_id,
        daily_incident_id,
        max(
            case when is_daily_last then comment_id else null end
        ) as comment_id,
        max(
            case when is_daily_last then incident_id else null end
        ) as incident_id,
        max(
            case when is_daily_last then comment_seq else null end
        ) as comment_seq,
        max(
            case when is_daily_last then comment_div else null end
        ) as comment_div,
        max(
            case when is_daily_last then comment_by else null end
        ) as comment_by,
        max(
            case when is_daily_last then comment_date else null end
        ) as comment_date,
        max(case when is_daily_last then ball_on else null end) as ball_on,
        sum(elapsed_days) as elapsed_days,
        sum(elapsed_days_on_dev) as elapsed_days_on_dev,
        sum(elapsed_days_on_field) as elapsed_days_on_field,
        sum(elapsed_days_on_unknown) as elapsed_days_on_unknown,
        sum(comment_count) as comment_count,
        sum(registered_count) as registered_count,
        sum(patch_planned_count) as patch_planned_count,
        sum(close_count) as close_count,
        sum(close_count_normal) as close_count_normal,
        sum(close_count_force) as close_count_force,
        sum(force_close_notice_count) as force_close_notice_count
    from
        data_for_mart_added
    group by
        date_id,
        daily_incident_id
)

select * from final
