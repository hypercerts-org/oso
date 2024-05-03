{# 
  TODO: this should go into a yml file for doc generation
  Summary GitHub metrics for a collection:
    - first_commit_date: The date of the first commit to the collection
    - last_commit_date: The date of the last commit to the collection
    - repos: The number of repositories in the collection
    - stars: The number of stars the collection has
    - forks: The number of forks the collection has
    - contributors: The number of contributors to the collection
    - contributors_6_months: The number of contributors to the collection in the last 6 months
    - new_contributors_6_months: The number of new contributors to the collection in the last 6 months    
    - avg_fulltime_devs_6_months: The number of full-time developers in the last 6 months
    - avg_active_devs_6_months: The average number of active developers in the last 6 months
    - commits_6_months: The number of commits to the collection in the last 6 months
    - issues_opened_6_months: The number of issues opened in the collection in the last 6 months
    - issues_closed_6_months: The number of issues closed in the collection in the last 6 months
    - pull_requests_opened_6_months: The number of pull requests opened in the collection in the last 6 months
    - pull_requests_merged_6_months: The number of pull requests merged in the collection in the last 6 months
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  artifact_source,
  first_commit_date,
  last_commit_date,
  repositories as `repository_count_all`,
  stars as `star_count_all`,
  forks as `fork_count_all`,
  contributors as `contributor_count_all`,
  contributors_6_months as `contributor_count_6_months`,
  new_contributors_6_months as `new_contributors_count_6_months`,
  avg_fulltime_devs_6_months as `fulltime_developer_count_6_months`,
  avg_active_devs_6_months as `active_developer_count_6_months`,
  commits_6_months as `commit_count_6_months`,
  issues_opened_6_months as `opened_issue_count_6_months`,
  issues_closed_6_months as `closed_issue_count_6_months`,
  pull_requests_opened_6_months as `opened_pull_request_count_6_months`,
  pull_requests_merged_6_months as `merged_pull_request_count_6_months`
from {{ ref('int_code_metrics_by_collection') }}
