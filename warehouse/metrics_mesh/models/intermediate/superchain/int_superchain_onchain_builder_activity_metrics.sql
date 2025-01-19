MODEL (
  name metrics.int_superchain_onchain_builder_activity_metrics,
  kind FULL,
);

@DEF(lookback_days, 30);

with project_metrics as (
  select
    events.to_project_id as project_id,
    events.event_source,
    sum(
      case
        when events.event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
          then events.amount / 1e18 -- TODO: remove gas_price
        else 0
      end
    ) as total_gas_used,
    sum(
      case
        when events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
          then events.amount
        else 0
      end
    ) as total_transactions,
    approx_count_distinct(events.from_artifact_id) as total_addresses
  from metrics.int_superchain_filtered_events events
  inner join metrics.int_artifacts_by_project as artifacts
    on events.to_artifact_id = artifacts.artifact_id
  where date(events.time) >= (current_date() - interval @lookback_days day)
  group by
    events.to_project_id,
    events.event_source
)

select
  project_metrics.*,
  projects.project_name,
  projects.display_name
from project_metrics
inner join metrics.int_projects as projects
  on project_metrics.project_id = projects.project_id
