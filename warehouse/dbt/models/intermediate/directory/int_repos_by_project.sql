with github_stats as (
  select
    to_id as artifact_id,
    MIN(time) as first_commit_time,
    MAX(time) as last_commit_time,
    COUNT(distinct TIMESTAMP_TRUNC(time, day)) as days_with_commits_count,
    COUNT(distinct from_id) as contributors_to_repo_count
  from {{ ref('int_events_to_project') }}
  where event_type = 'COMMIT_CODE'
  group by to_id
)

select
  p.project_id,
  p.project_source,
  p.project_namespace,
  p.project_name,
  r.artifact_id,
  r.owner as repo_owner,
  r.name as repo_name,
  r.is_fork,
  r.fork_count,
  r.star_count,
  s.first_commit_time,
  s.last_commit_time,
  s.days_with_commits_count,
  s.contributors_to_repo_count,
  'GITHUB' as artifact_source,
  LOWER(r.owner) as artifact_namespace,
  LOWER(r.name_with_owner) as artifact_name
from {{ ref('int_ossd__repositories_by_project') }} as r
left join {{ ref('int_projects') }} as p
  on r.project_id = p.project_id
left join github_stats as s
  on r.artifact_id = s.artifact_id
