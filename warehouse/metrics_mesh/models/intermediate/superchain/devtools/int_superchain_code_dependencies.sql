MODEL (
  name metrics.int_superchain_code_dependencies,
  kind FULL,
);

with all_dependencies as (
  select distinct
    sbom.from_project_id as dependent_project_id,
    sbom.from_artifact_id as dependent_artifact_id,
    owners.package_owner_project_id as dependency_project_id,
    owners.package_owner_artifact_id as dependency_artifact_id,
    sbom.to_package_artifact_name as dependency_name,
    sbom.to_package_artifact_source as dependency_source
  from metrics.sboms_v0 as sbom
  inner join metrics.package_owners_v0 as owners
    on
      sbom.to_package_artifact_name = owners.package_artifact_name
      and sbom.to_package_artifact_source = owners.package_artifact_source
)

select *
from all_dependencies
where
  dependent_project_id in (
    select distinct project_id
    from metrics.int_superchain_onchain_builder_filter
  )
  and dependency_artifact_id in (
    select artifact_id
    from metrics.int_superchain_devtool_artifact_filter
  )
  and dependency_project_id != dependent_project_id