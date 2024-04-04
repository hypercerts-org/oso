{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_from_collection') }} AS e
WHERE e.collection_id IS NOT NULL
GROUP BY 1, 2, 3
