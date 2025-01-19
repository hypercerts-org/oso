MODEL (
  name metrics.int_superchain_devtool_artifact_filter,
  kind FULL,
);

@DEF(max_release_lookback_days, 180);

with eligible_projects as (
  select
    to_artifact_id as artifact_id,
    max(time) as last_release_date
  from @oso_source('bigquery.oso.timeseries_events_by_artifact_v0') events
  where event_type = 'RELEASE_PUBLISHED'
  group by to_artifact_id
),

union_all_artifacts as (
  select artifact_id
  from eligible_projects
  where
    date(last_release_date) >= (current_date() - interval @max_release_lookback_days day)
  union all
  select package_owner_artifact_id as artifact_id
  from metrics.package_owners_v0
)

select distinct artifact_id
from union_all_artifacts
