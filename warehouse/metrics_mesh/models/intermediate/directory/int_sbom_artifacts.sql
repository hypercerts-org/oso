MODEL (
  name metrics.int_sbom_artifacts,
  kind FULL,
);

with ranked_snapshots as (
  select
    artifact_source,
    package_source,
    package_version,
    snapshot_at,
    lower(artifact_namespace) as artifact_namespace,
    lower(artifact_name) as artifact_name,
    lower(package) as package,
    row_number() over (
      partition by
        artifact_source,
        artifact_namespace,
        artifact_name,
        package_source,
        package,
        package_version
      order by snapshot_at asc
    ) as row_num
  from @oso_source('bigquery.ossd.sbom')
),

sbom_artifacts as (
  select
    artifact_source,
    artifact_namespace,
    artifact_name,
    package_source,
    package,
    package_version,
    snapshot_at
  from ranked_snapshots
  where row_num = 1
),

deps_dev_packages as (
  select distinct
    sbom_artifact_source,
    package_artifact_name,
    package_github_owner,
    package_github_repo
  from metrics.int_packages
  where is_current_owner = true
)

select
  {#
    Because we use repo.id as the artifact_source_id for github, we need to lookup the artifact_id for the SBOM repo. If the artifact is not found, this will return null.
  #}
  all_repos.project_id,
  all_repos.artifact_id,
  sbom_artifacts.artifact_source,
  sbom_artifacts.artifact_namespace,
  sbom_artifacts.artifact_name,
  {#
    Because we only index packages that are found in OSSD, most of the time this will return a null package_artifact_id.
  #}
  all_packages.project_id as package_project_id,
  all_packages.artifact_id as package_artifact_id,
  sbom_artifacts.package_source as package_artifact_source,
  '' as package_artifact_namespace,
  sbom_artifacts.package as package_artifact_name,
  'GITHUB' as package_owner_source,
  sbom_artifacts.package_version as package_version,
  deps_dev_packages.package_github_owner,
  deps_dev_packages.package_github_repo,
  deps_dev_repos.artifact_id as package_github_artifact_id,
  deps_dev_repos.project_id as package_github_project_id,
  sbom_artifacts.snapshot_at
from sbom_artifacts
left outer join metrics.int_all_artifacts as all_repos
  on
    sbom_artifacts.artifact_namespace = all_repos.artifact_namespace
    and sbom_artifacts.artifact_name = all_repos.artifact_name
left outer join metrics.int_all_artifacts as all_packages
  on
    sbom_artifacts.package = all_packages.artifact_name
    and sbom_artifacts.package_source = all_packages.artifact_source
left outer join deps_dev_packages
  on
    sbom_artifacts.package_source = deps_dev_packages.sbom_artifact_source
    and sbom_artifacts.package = deps_dev_packages.package_artifact_name
left outer join metrics.int_all_artifacts as deps_dev_repos
  on
    deps_dev_packages.package_github_owner = deps_dev_repos.artifact_namespace
    and deps_dev_packages.package_github_repo = deps_dev_repos.artifact_name
