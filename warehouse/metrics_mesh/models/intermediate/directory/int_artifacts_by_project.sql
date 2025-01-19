MODEL (
  name metrics.int_artifacts_by_project,
  kind FULL
);

select distinct
  artifacts.artifact_id,
  artifacts.artifact_source_id,
  artifacts.artifact_source,
  artifacts.artifact_namespace,
  artifacts.artifact_name,
  artifacts.artifact_url,
  artifacts.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
from metrics.int_all_artifacts as artifacts
left join metrics.int_projects as projects
  on artifacts.project_id = projects.project_id
where artifacts.project_id is not null
