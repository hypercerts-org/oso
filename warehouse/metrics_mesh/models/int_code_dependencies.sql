MODEL (
  name metrics.int_code_dependencies,
  kind FULL
);
select distinct
  sbom.from_project_id as dependent_project_id, -- dependent project (eg, opensource-observer)
  sbom.from_artifact_id as dependent_artifact_id, -- dependent repo (eg, opensource-observer/oso)
  owners.package_owner_project_id as dependency_project_id, -- dependency project (eg, ethers)
  owners.package_owner_artifact_id as dependency_artifact_id -- dependency repo (eg, ethers-io/ethers.js)
from @oso_source('sboms_v0') as sbom
join @oso_source('package_owners_v0') as owners
  on sbom.to_package_artifact_name = owners.package_artifact_name
  and sbom.to_package_artifact_source = owners.package_artifact_source