select
  events.project_id,
  time_intervals.time_interval,
  'contributor_count' as metric,
  COUNT(distinct events.from_artifact_id) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.event_type in (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'ISSUE_OPENED'
  )
  and events.bucket_day >= time_intervals.start_date
group by
  events.project_id,
  time_intervals.time_interval
