with raw_data as (
    select
        *
    from
        {{ ref('stg_qaweb__incident_comments') }}
),

mst_comment_div as (
    select * from {{ ref('seed_qaweb__mst_comment_div') }}
),

comment_div_info_added as (
    select
        t.*,
        coalesce(m.comment_div, 'others') as comment_div_adjusted,
        coalesce(m.ball_on, 'unknown') as ball_on,
        coalesce(m.is_closer, false) as is_closer,
        coalesce(m.is_approver, false) as is_approver,
        coalesce(m.is_patch_planned, false) as is_patch_planned,
        coalesce(m.is_response, false) as is_response
    from
        raw_data as t
    left outer join mst_comment_div as m
        on
            m.comment_div = t.comment_div
),

max_min_seq as (
    select
        incident_id,
        max(comment_seq) as max_seq,
        min(
            case when is_response then comment_seq else null end
        ) as min_seq_ball_on_field,
        max(
            case when is_approver then null else comment_seq end
        ) as max_seq_without_approver,
        max(
            case when is_closer or is_approver then null else comment_seq end
        ) as max_seq_without_closer,
        max(comment_seq) as last_seq
    from
        comment_div_info_added
    group by incident_id
),

flags_added as (
    select
        t.*,
        case
            when t.comment_seq = m.min_seq_ball_on_field then true else false
        end as is_first_response,
        case
            when
                (t.is_closer or t.is_approver)
                and t.comment_seq = m.max_seq_without_closer + 1
                then true
            else false
        end as is_final_closer,
        case
            when t.comment_seq > m.max_seq_without_closer + 1 then true else
                false
        end as is_after_final_close,
        case
            when
                is_approver and t.comment_seq = m.max_seq_without_approver + 1
                then true
            else false
        end as is_final_approver,
        case
            when t.comment_seq = m.last_seq then true else false
        end as is_last_comment
    from
        comment_div_info_added as t
    left outer join max_min_seq m
        on m.incident_id = t.incident_id
),

mst_user_name_adjust as (
    select * from {{ ref('seed_qaweb__mst_user_name_adjust') }}
),

user_name_adjusted as (
    select
        t.*,
        coalesce(m.user_name_adjusted, comment_by) as comment_by_adjusted
    from
        flags_added as t
    left outer join mst_user_name_adjust as m
        on
            m.user_name = t.comment_by

),

next_comment_date_added as (
    select
        *,
        case
            when is_final_closer or is_final_approver
                then
                    coalesce(
                        lead(comment_date)
                            over (partition by incident_id order by comment_seq),
                        comment_date
                    )
            else
                lead(comment_date)
                    over (partition by incident_id order by comment_seq asc)
        end as next_comment_date
    from
        user_name_adjusted
),

days_after_comment_added as (
    select
        t.*,
        (next_comment_date - comment_date) as days_after_comment
    from
        next_comment_date_added as t
),

force_close_announce_added as (
    select
        t.*,
        case
            when comment ~ 'その後[の]?状況.*(連絡|回答)が[な無](ければ|い場合).*クローズ'
                then true
            else false
        end as is_force_close_announce
    from
        days_after_comment_added as t
),

force_close_added as (
    select
        t.*,
        case
            when comment
                ~ '(連絡.*(なか|ない|無|ありま).*クローズ.*新規(ＱＡ|QA)登録を)|(強制クローズ[と]?させていただきます.*場合.*新規(ＱＡ|QA登録))'
                then true
            else false
        end as is_force_close
    from
        force_close_announce_added as t
)

select
    comment_id,
    incident_id,
    comment_seq,
    comment_div_adjusted as comment_div,
    comment_div as comment_div_org,
    comment_by_adjusted as comment_by,
    comment_by as comment_by_org,
    comment_date,
    next_comment_date,
    days_after_comment,
    ball_on,
    is_first_response,
    is_closer,
    is_final_closer,
    is_after_final_close,
    is_approver,
    is_final_approver,
    is_last_comment,
    is_patch_planned,
    is_force_close_announce,
    is_force_close,
    comment
from
    force_close_added
