MERGE {{ source(destination_table).fqdn }} AS destination
USING (
  {{ select_query }}
) AS source
ON destination.{{ unique_column }} = source.{{ unique_column }}
  AND TIMESTAMP_TRUNC(destination.{{ time_partitioning.column }}, DAY) = TIMESTAMP_TRUNC(source.{{ time_partitioning.column }}, DAY)
WHEN MATCHED THEN
  UPDATE SET {{ source(destination_table).update_columns_with("destination", "source", exclude=[unique_column]) }}
WHEN NOT MATCHED THEN 
  INSERT ({{ source(destination_table).select_columns() }}) 
  VALUES ({{ source(destination_table).select_columns(prefix="source") }})
-- Delete anything that doesn't appear in the source. This effectively replaces
-- any data in partitions that are being scanned with this merge
WHEN NOT MATCHED BY SOURCE 
    DELETE