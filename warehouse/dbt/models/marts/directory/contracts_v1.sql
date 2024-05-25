{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  artifact_source,
  transaction_hash,
  block_timestamp,
  root_deployer_address,
  created_by_address,
  contract_address,
  originating_eoa_address,
  creator_type,
  contract_type
from {{ ref('int_contracts') }}