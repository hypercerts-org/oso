MODEL (
  name metrics.package_owners_v0,
  kind FULL
);

select distinct
  package_project_id,
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name,
  package_github_project_id as package_owner_project_id,
  package_github_artifact_id as package_owner_artifact_id,
  package_owner_source,
  package_github_owner as package_owner_artifact_namespace,
  package_github_repo as package_owner_artifact_name
from metrics.int_sbom_artifacts
