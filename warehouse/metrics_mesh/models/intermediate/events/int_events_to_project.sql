MODEL (
  name metrics.int_events_to_project,
  description 'All events to a project',
  kind FULL,
);

select
  artifacts.project_id,
  events.from_artifact_id,
  events.to_artifact_id,
  events.time,
  events.event_source,
  events.event_type,
  events.amount
from @oso_source('bigquery.oso.timeseries_events_by_artifact_v0') events
inner join metrics.int_artifacts_by_project artifacts
  on
    events.to_artifact_id
    = artifacts.artifact_id
