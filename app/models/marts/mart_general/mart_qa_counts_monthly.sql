select 
    t1.month_id,
	t1.monthly_incident_id,
    t2.title,
    t2.incident_div,
    t2.category,
    t2.hospital,
    t2.impact,
    t2.impact_by_register,
    t2.registered_date,
    t2.closed_date,
    t2.assigned_to,
    t2.is_assigned_to_dwh,
    t2."status",
    t2.has_patch_no,
    t2.has_patch_comment,
    t2.has_force_close_announce,
    t2.has_force_close,
    t2.has_library_change,
	t1.incident_id,
	t1.comment_id,
	t1.comment_seq,
	t1.comment_div,
	t1.comment_by,
	t1.comment_date,
	t1.ball_on,
	t1.elapsed_days,
	t1.elapsed_days_on_dev,
	t1.elapsed_days_on_field,
	t1.elapsed_days_on_unknown,
	t1.month_end_active_count,
	t1.month_end_active_count_dev,
	t1.month_end_active_count_field,
	t1.month_end_active_count_unknown,
	t1.comment_count,
	t1.registered_count,
	t1.patch_planned_count,
	t1.close_count,
	t1.close_count_normal,
	t1.close_count_force,
	t1.force_close_notice_count
from
    {{ ref("qa_counts_monthly") }} as t1
join
    {{ ref("qa_incidents") }} as t2
on
    t1.incident_id = t2.incident_id
where t1.month_id >=
    {{ get_first_date_of_financial_year(var('mart_scope_years')) }}
