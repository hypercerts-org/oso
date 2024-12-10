import logging
import typing as t
import uuid

from sqlglot import exp
from sqlmesh.core.dialect import parse_one
from trino.dbapi import Connection

logger = logging.getLogger(__name__)


class TrinoCacheExportManager:
    def __init__(self, db: Connection, gcs_bucket: str):
        self.exported_map: t.Dict[str, str] = {}
        self.gcs_bucket = gcs_bucket
        self.db = db

    def run_query(self, query: str):
        cursor = self.db.cursor()
        logger.info(f"EXECUTING: {query}")
        return cursor.execute(query)

    def export_table_for_cache(self, table: str):
        # Using the actual name
        # Export with trino
        if table in self.exported_map:
            logger.debug(f"CACHE HIT FOR {table}")
            return self.exported_map[table]

        columns: t.List[t.Tuple[str, str]] = []

        col_result = self.run_query(f"SHOW COLUMNS FROM {table}").fetchall()
        for row in col_result:
            column_name = row[0]
            column_type = row[1]
            columns.append((column_name, column_type))

        table_exp = exp.to_table(table)
        logger.info(f"RETREIVED COLUMNS: {columns}")
        export_table_name = f"export_{table_exp.this.this}_{uuid.uuid4().hex}"

        base_create_query = f"""
            CREATE table "source"."export"."{export_table_name}" (
                placeholder VARCHAR,
            ) WITH (
                format = 'PARQUET',
                external_location = 'gs://{self.gcs_bucket}/trino-export/{export_table_name}/'
            )
        """
        create_query = parse_one(base_create_query)
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(
                    this=exp.to_identifier(column_name),
                    kind=parse_one(column_type, into=exp.DataType),
                )
                for column_name, column_type in columns
            ],
        )

        self.run_query(create_query.sql(dialect="trino"))

        base_insert_query = f"""
            INSERT INTO "source"."export"."{export_table_name}" (placeholder)
            SELECT placeholder
            FROM {table_exp}
        """

        column_identifiers = [
            exp.to_identifier(column_name) for column_name, _ in columns
        ]

        insert_query = parse_one(base_insert_query)
        insert_query.this.set(
            "expressions",
            column_identifiers,
        )
        select = t.cast(exp.Select, insert_query.expression)
        select.set("expressions", column_identifiers)

        self.run_query(insert_query.sql(dialect="trino"))

        self.exported_map[table] = export_table_name
        return self.exported_map[table]
