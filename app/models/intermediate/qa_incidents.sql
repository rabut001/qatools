
/*
  On the first, removing columns which have long data like "comment_history"
  for performance reason.
  This comes from the characteristic of PostgreSQL.
  In other database, you might able to use simple "select *" here.
*/
with raw_data as (
    select
        incident_id,
        title,
        incident_div,
        category,
        category2,
        category3,
        hospital,
        registered_by,
        registered_date,
        first_response_date,
        close_date,
        approved_date,
        impact,
        impact_by_register,
        related_incident,
        assigned_to,
        patch_no,
        "status",
        "server",
        "version",
        version_ehr,
        last_updated_date,
        critical,
        "event",
        event_date,
        external_case_id,
        additional_item1,
        additional_item2,
        additional_item3,
        additional_item4,
        has_library_change
    from
        {{ ref('stg_qaweb__incidents') }}
),

-- Removing long data columns first for the same reason
comments as (
    select
        incident_id,
        comment_div,
        comment_date,
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
        is_force_close
    from
        {{ ref('qa_incident_comments') }}
),

comment_data as (
    select
        incident_id,
        min(
            case when is_first_response then comment_date else null end
        ) as first_response_date_by_comment,
        max(
            case when is_final_closer then comment_date else null end
        ) as close_date_by_comment,
        max(
            case when is_final_approver then comment_date else null end
        ) as approved_date_by_comment,
        max(comment_date) as last_comment_date,
        bool_or(is_patch_planned) as has_patch,
        bool_or(is_force_close_announce) as has_force_close_announce,
        bool_or(is_force_close and is_final_closer) as has_force_close,
        sum(
            case when ball_on = 'dev' then days_after_comment else 0 end
        ) as days_on_developer,
        sum(
            case when ball_on = 'field' then days_after_comment else 0 end
        ) as days_on_field,
        sum(
            case when ball_on = 'unknown' then days_after_comment else 0 end
        ) as days_on_unknown,
        max(
            case when is_last_comment then comment_div else null end
        ) as status_by_comment,
        max(
            case when is_last_comment then ball_on else null end
        ) as ball_on
    from
        comments
    group by incident_id
),

comment_data_added as (
    select
        t.*,
        t2.first_response_date_by_comment,
        t2.close_date_by_comment,
        t2.approved_date_by_comment,
        t2.last_comment_date,
        t2.has_patch,
        t2.has_force_close_announce,
        t2.has_force_close,
        (
            t2.first_response_date_by_comment - t.registered_date
        ) as days_before_first_response,
        t2.days_on_developer,
        t2.days_on_field,
        t2.days_on_unknown,
        t2.ball_on,
        t2.status_by_comment
    from
        raw_data t
    left outer join comment_data t2
        on t2.incident_id = t.incident_id

),

mst_user_name_adjust as (
    select * from {{ ref('seed_qaweb__mst_user_name_adjust') }}
),

user_name_adjusted as (
    select
        t.*,
        coalesce(
            m1.user_name_adjusted, registered_by
        ) as registered_by_adjusted,
        coalesce(m1.user_name_adjusted, assigned_to) as assigned_to_adjusted
    from
        comment_data_added as t
    left outer join mst_user_name_adjust as m1
        on
            m1.user_name = t.assigned_to
    left outer join mst_user_name_adjust as m2
        on
            m2.user_name = t.registered_by

),

mst_user_dwh_dev as (
    select * from {{ ref('seed_qaweb__mst_user_dwh_dev') }}
),

is_assigned_to_dwh_added as (
    select
        t.*,
        case
            when
                m.user_name is not null or t.assigned_to is null
                then true
            else false
        end as is_assigned_to_dwh
    from
        user_name_adjusted as t
    left outer join mst_user_dwh_dev as m
        on m.user_name = t.assigned_to_adjusted

),

final as (
    select
        incident_id,
        title,
        incident_div,
        category,
        category2,
        category3,
        hospital,
        registered_by_adjusted as registered_by,
        registered_by as registered_by_org,
        registered_date,
        impact,
        impact_by_register,
        assigned_to_adjusted as assigned_to,
        assigned_to as assigned_to_org,
        is_assigned_to_dwh,
        status_by_comment as "status",
        "status" as status_org,
        ball_on,
        first_response_date_by_comment as first_response_date,
        first_response_date as first_response_date_org,
        close_date_by_comment as closed_date,
        close_date as closed_date_org,
        approved_date_by_comment as approved_date,
        approved_date as approved_date_org,
        last_comment_date,
        last_updated_date,
        patch_no,
        case when patch_no is not null then true else false end as has_patch_no,
        has_patch as has_patch_comment,
        has_force_close_announce,
        has_force_close,
        has_library_change,
        days_before_first_response,
        days_on_developer,
        days_on_field,
        days_on_unknown,
        "server",
        "version",
        version_ehr,
        critical,
        "event",
        event_date,
        external_case_id,
        additional_item1,
        additional_item2,
        additional_item3,
        additional_item4,
        related_incident
    from
        is_assigned_to_dwh_added
)

select * from final
