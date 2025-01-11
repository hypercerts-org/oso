import logging
import typing as t
from datetime import datetime
from urllib.parse import urlparse

from clickhouse_connect.driver.client import Client
from metrics_tools.compute.types import ExportReference, ExportType, TableReference
from metrics_tools.transfer.base import ImporterInterface
from oso_dagster.utils.clickhouse import (
    create_table,
    drop_table,
    import_data,
    rename_table,
)

logger = logging.getLogger(__name__)


class ClickhouseImporter(ImporterInterface):
    def __init__(self, ch: Client, log_override: t.Optional[logging.Logger] = None):
        self.ch = ch
        self.logger = log_override or logger

    def supported_types(self):
        return {ExportType.GCS}

    async def import_table(
        self,
        destination_table: TableReference,
        export_reference: ExportReference,
    ):
        if export_reference.type != ExportType.GCS:
            raise NotImplementedError(
                f"Unsupported export type: {export_reference.type}"
            )
        gcs_path = export_reference.payload["gcs_path"]
        parsed_gcs_path = urlparse(gcs_path)
        gcs_bucket = parsed_gcs_path.netloc
        gcs_blob_path = parsed_gcs_path.path.strip("/")

        # Write the table to a temporary location in clickhouse (we will rename the table later)
        loading_table_fqn = (
            f"{destination_table.fqn}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.logger.debug(f"Creating table {loading_table_fqn}")
        create_table(
            self.ch,
            loading_table_fqn,
            export_reference.columns.columns_as("clickhouse"),
        )
        import_path = f"https://storage.googleapis.com/{gcs_bucket}/{gcs_blob_path}/*"
        self.logger.debug(f"Importing table {loading_table_fqn} from {gcs_path}")
        import_data(
            self.ch,
            loading_table_fqn,
            import_path,
            format="Parquet",
        )
        final_table_fqn = destination_table.fqn

        # Drop existing table if it exists
        self.logger.debug(f"Dropping table {destination_table.fqn}")
        drop_table(self.ch, final_table_fqn)

        # Rename the table to the final destination
        self.logger.debug(f"Renaming table {loading_table_fqn} to {final_table_fqn}")
        rename_table(self.ch, loading_table_fqn, final_table_fqn)

        self.logger.debug(f"Table {final_table_fqn} imported successfully")