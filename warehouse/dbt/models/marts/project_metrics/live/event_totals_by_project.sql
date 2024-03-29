{# 
  This model calculates the total amount of events for each project and namespace
  for different time intervals. The time intervals are defined in the `time_ranges` CTE.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

WITH time_ranges AS (
  SELECT '30D' AS time_interval, DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AS start_date UNION ALL
  SELECT '90D' AS time_interval, DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) UNION ALL
  SELECT '6M' AS time_interval, DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH) UNION ALL
  SELECT '1Y' AS time_interval, DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR) UNION ALL
  SELECT 'ALL' AS time_interval, DATE('1970-01-01') 
),
aggregated_data AS (
  SELECT 
    e.project_id,
    e.from_namespace AS namespace,
    e.event_type,
    TR.time_interval,
    SUM(e.amount) AS amount    
  FROM {{ ref('events_daily_to_project_by_source') }} AS e
  CROSS JOIN time_ranges AS TR
  WHERE DATE(e.bucket_day) >= TR.start_date
  GROUP BY 1, 2, 3, 4
)
SELECT 
  project_id,
  namespace,
  CONCAT(event_type, '_TOTAL_', time_interval) AS impact_metric,
  SUM(amount) AS amount
FROM aggregated_data
GROUP BY project_id, namespace, time_interval, event_type
ORDER BY project_id, namespace, time_interval, event_type
