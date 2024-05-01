{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  project_id,
  namespace AS project_namespace,
  project_slug,
  project_name
FROM {{ ref('int_projects') }}
