MODEL (
  name metrics.sboms_v0,
  kind FULL
);

select distinct
  project_id as from_project_id,
  artifact_id as from_artifact_id,
  artifact_source as from_artifact_source,
  artifact_namespace as from_artifact_namespace,
  artifact_name as from_artifact_name,
  package_project_id as to_package_project_id,
  package_artifact_id as to_package_artifact_id,
  package_artifact_source as to_package_artifact_source,
  package_artifact_namespace as to_package_artifact_namespace,
  package_artifact_name as to_package_artifact_name
from metrics.int_sbom_artifacts
