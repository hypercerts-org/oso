MODEL (
  name metrics.contracts_v0,
  kind FULL
);

select distinct
  network as artifact_source,
  deployer_address as root_deployer_address,
  contract_address
from metrics.int_derived_contracts