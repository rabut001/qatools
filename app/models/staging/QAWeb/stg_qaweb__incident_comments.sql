with base_data as (
    {{ get_adjusted_data("base_qaweb__incident_comments") }}
),

key_added as (
    select
        incident_id || '_' || to_char(comment_seq, 'FM0000') as comment_id,
        *
    from
        base_data
),

-- adjust direct close data (add dummy comment records for direct close)
incidents as (
    select * from {{ ref("stg_qaweb__incidents") }}
),

mst_incident_div as (
    select * from {{ ref("seed_qaweb__mst_comment_div") }}
),

max_seq as (
    select incident_id, max(comment_seq) as max_seq
    from key_added
    group by incident_id
),

direct_close as (
    select
        i.incident_id || to_char(max_seq + 1, 'FM0000') as comment_id,
        i.incident_id,
        max_seq.max_seq + 1 as incident_seq,
        '完了へ直接変更' as comment_div,
        '(dummy)' as comment_by,
        i.close_date as comment_date,
        '(ライブラリ変更などによりステータスを直接完了に変更)' as comment
    from
        incidents i
    left join max_seq
        on max_seq.incident_id = i.incident_id
    where
        i.close_date is not null
        and not exists (
            select 1
            from key_added as t
            where t.incident_id = i.incident_id
                and t.comment_div in (
                    select comment_div
                    from mst_incident_div
                    where is_closer = true or is_approver = true
                )
        )
),

direct_close_added as (
    select * from key_added
    union all
    select * from direct_close
)

select
    comment_id,
    incident_id,
    comment_seq,
    comment_div,
    comment_by,
    comment_date,
    comment
from
    direct_close_added
