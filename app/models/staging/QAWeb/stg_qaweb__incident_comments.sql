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

mst_comment_div as (
    select * from {{ ref("seed_qaweb__mst_comment_div") }}
),

max_comment as (
    select
        incident_id,
        comment_seq,
        comment_div,
        comment_date
    from
        (select
            incident_id,
            comment_seq,
            comment_div,
            comment_date,
            row_number()
                over (partition by incident_id order by comment_seq desc)
            as no_for_filter
        from key_added) as a
    where
        no_for_filter = 1
),

direct_close as (
    select
        i.incident_id || to_char(c.comment_seq + 1, 'FM0000') as comment_id,
        i.incident_id,
        c.comment_seq + 1 as comment_seq,
        '完了へ直接変更' as comment_div,
        '(dummy)' as comment_by,
        i.close_date as comment_date,
        '(ライブラリ変更などによりステータスを直接完了に変更)' as comment
    from
        incidents i
    left join max_comment as c
        on c.incident_id = i.incident_id
    left join mst_comment_div m
        on m.comment_div = c.comment_div
    where
        i.close_date is not null
        and i.close_date >= c.comment_date
        and (m.comment_div is null or (not m.is_closer and not m.is_approver))
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
