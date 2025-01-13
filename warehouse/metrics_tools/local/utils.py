import os
import typing as t

import duckdb
from google.cloud import bigquery

project_id = os.getenv("GOOGLE_PROJECT_ID")


def bq_to_duckdb(table_mapping: t.Dict[str, str], duckdb_path: str):
    """Copies the tables in table_mapping to tables in duckdb

    The table_mapping is in the form { "bigquery_table_fqn": "duckdb_table_fqn" }
    """
    bqclient = bigquery.Client(project=project_id)
    conn = duckdb.connect(duckdb_path)

    conn.sql("CREATE SCHEMA IF NOT EXISTS sources;")

    for bq_table, duckdb_table in table_mapping.items():
        table = bigquery.TableReference.from_string(bq_table)
        rows = bqclient.list_rows(table)

        table_as_arrow = rows.to_arrow(create_bqstorage_client=True)  # noqa: F841

        conn.sql(
            f"""
            CREATE TABLE IF NOT EXISTS {duckdb_table} AS 
            SELECT * FROM table_as_arrow
        """
        )


def initialize_local_duckdb(path: str):
    bq_to_duckdb(
        {
            # We need to rename this once we run the oso_playground dbt again
            "opensource-observer.oso_playground.timeseries_events_by_artifact_v0": "sources.timeseries_events_by_artifact_v0",
            "opensource-observer.oso_playground.artifacts_by_project_v1": "sources.artifacts_by_project_v1",
            "opensource-observer.oso_playground.projects_by_collection_v1": "sources.projects_by_collection_v1",
            "opensource-observer.oso_playground.timeseries_events_aux_issues_by_artifact_v0": "sources.timeseries_events_aux_issues_by_artifact_v0",
            "opensource-observer.oso.sboms_v0": "sources.sboms_v0",
            "opensource-observer.oso.package_owners_v0": "sources.package_owners_v0",
        },
        path,
    )


def reset_local_duckdb(path: str):
    conn = duckdb.connect(path)

    response = conn.query("SHOW ALL TABLES")
    schema_names = response.df()["schema"].unique().tolist()
    for schema_name in schema_names:
        if schema_name != "sources":
            print(f"dropping schema {schema_name}")
            conn.query(f"DROP schema {schema_name} cascade")
