with base_data as (
    {{ get_adjusted_data("base_qaweb__incidents") }}
),

library_change_added as (
    select
        t.*,
        case
            when description like '%★★★★★★★★★★★★★★★★★★★%'
                and description like '%ライブラリの変更が完了しました%'
                then true
            else false
        end as has_library_change
    from
        base_data as t
)

select * from library_change_added
