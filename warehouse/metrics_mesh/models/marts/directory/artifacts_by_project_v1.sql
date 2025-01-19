MODEL (
  name metrics.artifacts_by_project_v1,
  kind FULL
);

select
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  project_id,
  project_source,
  project_namespace,
  project_name
from metrics.int_artifacts_by_project
