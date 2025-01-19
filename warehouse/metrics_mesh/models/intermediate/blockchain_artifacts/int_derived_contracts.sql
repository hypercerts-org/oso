MODEL (
  name metrics.int_derived_contracts,
  kind FULL,
);

with contracts_deployed_no_factory as (
  select
    network,
    deployer_address,
    contract_address
  from @oso_source('bigquery.oso.int_deployers')
  where contract_address is not null
),

contracts_deployed_via_factory as (
  {# 
    This gets all of the contracts deployed by any factory.

    Deployer Address is the EOA address that started the transaction
  #}
  select
    network,
    originating_address as deployer_address,
    contract_address as contract_address
  from @oso_source('bigquery.oso.int_factories')
  where contract_address is not null
),

contracts_deployed_by_safe_or_known_proxy as (
  {# 
    This gets all of the contracts deployed by a safe or other known proxy
    Deployer address is a proxy (safe or other known proxy) that deployed the contract
  #}
  select
    factories.network,
    proxies.address as deployer_address,
    factories.contract_address as contract_address
  from @oso_source('bigquery.oso.int_factories') as factories
  inner join @oso_source('bigquery.oso.int_proxies') as proxies
    on
      factories.originating_contract = proxies.address
      and factories.network = proxies.network
  where contract_address is not null
),

derived_contracts as (
  select
    network,
    deployer_address,
    contract_address
  from contracts_deployed_no_factory

  union all

  select
    network,
    deployer_address,
    contract_address
  from contracts_deployed_via_factory

  union all

  select
    network,
    deployer_address,
    contract_address
  from contracts_deployed_by_safe_or_known_proxy
)

select distinct
  network,
  deployer_address,
  contract_address
from derived_contracts
