{{
  config(
    materialized='table',
  ) if target.name in ['playground', 'dev'] else config(
    enabled=false,
  )
}}
select *
from {{ source("optimism", 'receipts') }}
where block_timestamp >= TIMESTAMP_TRUNC(
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), interval 1 day),
  day
)
