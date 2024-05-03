{{
  config(
    materialized='incremental',
    partition_by={
      "field": "block_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="transaction_hash",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  ) if target.name == 'production' else config(
    materialized='table',
  )
}}

select
  block_timestamp,
  `hash` as transaction_hash,
  from_address as deployer_address,
  receipt_contract_address as contract_address
from {{ source("ethereum", "transactions") }}
where
  to_address is null
  and receipt_status = 1
  and receipt_contract_address is not null
{% if is_incremental() %}
    and block_timestamp >= (
      select max(block_timestamp)
      from {{ this }}
    )
    and block_timestamp < timestamp_trunc(current_timestamp(), day)
  {% endif %}
