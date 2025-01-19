MODEL (
  name metrics.int_collections,
  description 'All collections',
  kind FULL,
);

select
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
from @oso_source('bigquery.oso.stg_ossd__current_collections') as collections
