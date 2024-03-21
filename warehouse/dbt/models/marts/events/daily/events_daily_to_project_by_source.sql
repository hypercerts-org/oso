{# 
  All events daily to a project by source
#}

SELECT
  e.project_id,
  e.from_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1, 2, 3, 4
