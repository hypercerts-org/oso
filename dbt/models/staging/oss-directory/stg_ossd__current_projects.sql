{# 
  The most recent view of projects from the ossd cloudquery plugin.
#}
WITH most_recent_sync AS (
  SELECT 
    MAX(_cq_sync_time) AS sync_time
  FROM `oso-production.opensource_observer.projects_ossd`
)
SELECT 
  {# 
    id is the SHA256 of namespace + slug. We hardcode our namespace
    "oso" for now but we are assuming we will allow users to add their on the
    OSO website
  #}
  SHA256(CONCAT("oso", slug)) as id,
  "oso" as namespace,
  p.* 
FROM `oso-production.opensource_observer.projects_ossd` as p
WHERE _cq_sync_time = (SELECT * FROM most_recent_sync)