select distinct
  project_id,
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url
from {{ ref('int_all_artifacts') }}
