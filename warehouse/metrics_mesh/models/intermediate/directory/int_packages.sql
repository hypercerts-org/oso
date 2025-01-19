MODEL (
  name metrics.int_packages,
  kind FULL,
);

with deps_dev as (
  select
    'Version' as package_version,
    upper('System') as package_artifact_source,
    lower('Name') as package_artifact_name,
    lower(split('ProjectName', '/')[0]) as package_github_owner,
    lower(split('ProjectName', '/')[1]) as package_github_repo
  from @oso_source('bigquery.oso.stg_deps_dev__packages')
),

latest_versions as (
  select
    package_artifact_source,
    package_artifact_name,
    package_github_owner as current_owner,
    package_github_repo as current_repo
  from deps_dev
  qualify row_number() over (
    partition by package_artifact_name, package_artifact_source
    order by package_version desc
  ) = 1
)

select
  deps_dev.package_artifact_source,
  deps_dev.package_artifact_name,
  deps_dev.package_version,
  deps_dev.package_github_owner,
  deps_dev.package_github_repo,
  case
    when deps_dev.package_artifact_source = 'CARGO' then 'RUST'
    when deps_dev.package_artifact_source = 'NPM' then 'NPM'
    when deps_dev.package_artifact_source = 'PYPI' then 'PIP'
    when deps_dev.package_artifact_source = 'GO' then 'GO'
    when deps_dev.package_artifact_source = 'MAVEN' then 'MAVEN'
    when deps_dev.package_artifact_source = 'NUGET' then 'NUGET'
    else 'UNKNOWN'
  end as sbom_artifact_source,
  (
    deps_dev.package_github_owner = latest_versions.current_owner
    and deps_dev.package_github_repo = latest_versions.current_repo)
    as is_current_owner
from deps_dev
left join latest_versions
  on
    deps_dev.package_artifact_source = latest_versions.package_artifact_source
    and deps_dev.package_artifact_name = latest_versions.package_artifact_name
