MODEL (
  name metrics.int_projects,
  description 'All projects',
  kind FULL,
);

select
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name,
  description,
  ARRAY_LENGTH(github)
    as github_artifact_count,
  ARRAY_LENGTH(blockchain)
    as blockchain_artifact_count,
  ARRAY_LENGTH(npm)
    as npm_artifact_count
from @oso_source('bigquery.oso.stg_ossd__current_projects')
