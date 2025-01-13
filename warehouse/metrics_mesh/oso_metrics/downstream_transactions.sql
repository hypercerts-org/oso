select
  @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  code_dependencies.dependency_artifact_id as to_artifact_id,
  '' as from_artifact_id,
  @metrics_name() as metric,
  SUM(tm.amount) as amount
from @metrics_peer_ref(
    transactions,
    time_aggregation := @time_aggregation,
  ) as transactions
join metrics.artifacts_by_project_v1 as abp
  on transactions.to_artifact_id = abp.artifact_id
join metrics.int_code_dependencies as code_dependencies
  on abp.project_id = code_dependencies.dependent_project_id
-- We can get the rolled up data for transactions 
where event_type in ('CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT')
  and events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source