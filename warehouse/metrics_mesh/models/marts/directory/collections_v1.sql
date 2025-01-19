MODEL (
  name metrics.collections_v1,
  kind FULL
);

select
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
from metrics.int_collections as collections
