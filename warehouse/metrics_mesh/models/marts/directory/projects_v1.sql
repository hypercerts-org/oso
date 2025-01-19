MODEL (
  name metrics.projects_v1,
  kind FULL
);

select
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  projects.display_name,
  projects.description
from metrics.int_projects as projects