MODEL(
  name metrics.downstream_transactions,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 365,
    batch_concurrency 1
  )
);
select
  owners.package_owner_project_id as package_owner_project_id,
  tm.sample_date::DATE as sample_date,
  tm.metric_id::TEXT as metric_id,
  tm.unit::TEXT as unit,
  sum(tm.amount)::FLOAT as downstream_amount
from @oso_source('sboms_v0') as sbom
join @oso_source('package_owners_v0') as owners
  on sbom.to_package_artifact_name = owners.package_artifact_name
  and sbom.to_package_artifact_source = owners.package_artifact_source
join metrics.timeseries_metrics_by_project_v0 as tm
  on sbom.from_project_id = tm.project_id
group by 1,2,3,4