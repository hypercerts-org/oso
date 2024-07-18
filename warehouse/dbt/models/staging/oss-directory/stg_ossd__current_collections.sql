{# 
  The most recent view of collections from the ossd cloudquery plugin.
#}

select
  {# 
    id is the SHA256 of namespace + slug. We hardcode our namespace
    "oso" for now but we are assuming we will allow users to add their on the
    OSO website
  #}
  {{ oso_id('"oso"', 'name') }} as collection_id,
  "OSS_DIRECTORY" as collection_source,
  "oso" as collection_namespace,
  collections.name as collection_name,
  collections.display_name,
  collections.description,
  collections.projects,
  collections.sha as committed_sha,
  collections.committed_time as sync_time
from {{ oso_source('ossd', 'collections') }} as collections
