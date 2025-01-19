MODEL (
  name metrics.artifacts_by_collection_v1,
  kind FULL
);

select
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  collection_id,
  collection_source,
  collection_namespace,
  collection_name
from metrics.int_artifacts_by_collection
