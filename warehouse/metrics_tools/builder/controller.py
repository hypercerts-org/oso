"""Wraps the sqlmesh controller from dagster sqlmesh to provide a richer
experience specifically for creating metrics models"""

import logging
import os
import typing as t
import sqlglot as sql
from sqlglot import exp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


from dagster_sqlmesh.controller.base import SQLMeshController, SQLMeshInstance

logger = logging.getLogger(__name__)


class MetricsController:
    @classmethod
    def setup(
        cls,
        path: str,
        environment: str = "test",
        gateway: str = "local",
        enable_logging: bool = False,
        log_override: t.Optional[logging.Logger] = None,
    ):
        if enable_logging:
            import sys

            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        controller = SQLMeshController.setup(
            path=path,
            gateway=gateway,
            log_override=log_override,
        )
        os.environ["SQLMESH_TIMESERIES_METRICS_START"] = "2024-07-01"
        return cls(environment, controller)

    def __init__(self, environment: str, sqlmesh_controller: SQLMeshController):
        self._environment = environment
        self._sqlmesh_controller = sqlmesh_controller

    def load(self):
        # Debug console
        with self._sqlmesh_controller.instance(self._environment) as mesh:
            for event in mesh.plan_and_run(
                plan_options={"skip_tests": True},
            ):
                logger.debug(f"event received: {event.__class__.__name__}")
                logger.debug(event)

    def models_dag(self):
        with self._sqlmesh_controller.instance(self._environment) as mesh:
            return mesh.models_dag()

    def plot(self, query: str, group_by: str):
        with self._sqlmesh_controller.instance(self._environment) as mesh:
            df = self._fetchdf(mesh, query)
            for entity_id, group in df.groupby(group_by):
                print(group.dtypes)
                print(entity_id)
                plt.plot(
                    group["metrics_sample_date"],
                    group["amount"],
                    label=f"Entity {entity_id}",
                )

            # Add labels, title, and legend
            plt.xlabel("Time")
            dt_fmt = mdates.DateFormatter("%Y-%m-%d")
            plt.locator_params(nbins=5)
            plt.gca().xaxis.set_major_formatter(dt_fmt)
            plt.ylabel("Amount")
            plt.title("Metrics Over Time by Project ID")
            plt.grid(True)
            plt.show()
            return df

    def fetchdf(self, query: str):
        with self._sqlmesh_controller.instance(self._environment) as mesh:
            return self._fetchdf(mesh, query)

    def _fetchdf(self, mesh: SQLMeshInstance, query: str):
        parsed = sql.parse_one(query)
        for table in parsed.find_all(exp.Table):
            table_name = table.this
            db_name = table.db
            try:
                rewritten_table = mesh.context.table(f"{db_name}.{table_name}")
            except KeyError:
                continue
            print(f"rewriting: {rewritten_table}")
            rewritten = exp.to_table(rewritten_table)
            if table.alias:
                rewritten = rewritten.as_(table.alias, table=True)
            table.replace(rewritten)

        print(parsed.sql(dialect="duckdb"))
        return mesh.context.fetchdf(parsed.sql(dialect="duckdb"))
