"""Run metrics queries for a given boundary"""

import duckdb
import arrow
import logging
from metrics_tools.utils.glot import str_or_expressions
from sqlmesh.core.context import ExecutionContext
from sqlmesh.core.config import DuckDBConnectionConfig
from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter
from sqlmesh.core.macros import RuntimeStage

from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.intermediate import run_macro_evaluator
from metrics_tools.factory.macros import (
    metrics_end,
    metrics_sample_date,
    metrics_start,
)
from metrics_tools.models import create_unregistered_macro_registry
import pandas as pd
import abc

from datetime import datetime
import typing as t

from sqlglot import exp

logger = logging.getLogger(__name__)


def generate_duckdb_create_table(df: pd.DataFrame, table_name: str) -> str:
    # Map Pandas dtypes to DuckDB types
    dtype_mapping = {
        "int64": "BIGINT",
        "int32": "INTEGER",
        "float64": "DOUBLE",
        "float32": "FLOAT",
        "bool": "BOOLEAN",
        "object": "TEXT",
        "datetime64[ns]": "TIMESTAMP",
        "datetime64[us]": "TIMESTAMP",
        "timedelta64[ns]": "INTERVAL",
    }

    # Start the CREATE TABLE statement
    create_statement = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"

    # Generate column definitions
    column_definitions = []
    for col in df.columns:
        col_type = dtype_mapping.get(
            str(df[col].dtype), "TEXT"
        )  # Default to TEXT for unknown types
        column_definitions.append(f"    {col} {col_type}")

    # Join the column definitions and finish the statement
    create_statement += ",\n".join(column_definitions)
    create_statement += "\n);"

    return create_statement


class RunnerEngine(abc.ABC):
    def execute_df(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("execute_df not implemented")

    def execute(self, query: str):
        raise NotImplementedError("execute_df not implemented")


class ExistingDuckDBConnectionConfig(DuckDBConnectionConfig):
    def __init__(self, conn: duckdb.DuckDBPyConnection, *args, **kwargs):
        self._existing_connection = conn
        super().__init__(*args, **kwargs)

    @property
    def _connection_factory(self) -> t.Callable:
        return lambda: self._existing_connection


class MetricsRunner:
    @classmethod
    def create_duckdb_execution_context(
        cls,
        conn: duckdb.DuckDBPyConnection,
        query: str | t.List[exp.Expression],
        ref: PeerMetricDependencyRef,
        locals: t.Optional[t.Dict[str, t.Any]],
    ):
        def connection_factory():
            return conn

        engine_adapter = DuckDBEngineAdapter(connection_factory)
        context = ExecutionContext(engine_adapter, {})
        return cls(context, str_or_expressions(query), ref, locals)

    @classmethod
    def from_sqlmesh_context(
        cls,
        context: ExecutionContext,
        query: str | t.List[exp.Expression],
        ref: PeerMetricDependencyRef,
        locals: t.Optional[t.Dict[str, t.Any]] = None,
    ):
        return cls(context, str_or_expressions(query), ref, locals)

    def __init__(
        self,
        context: ExecutionContext,
        query: t.List[exp.Expression],
        ref: PeerMetricDependencyRef,
        locals: t.Optional[t.Dict[str, t.Any]] = None,
    ):
        self._context = context
        self._query = query
        self._ref = ref
        self._locals = locals or {}

    def run(self, start: datetime, end: datetime):
        """Run metrics for a given period and return the results as pandas dataframes"""
        if self._ref.get("time_aggregation"):
            return self.run_time_aggregation(start, end)
        else:
            return self.run_rolling(start, end)

    def run_time_aggregation(self, start: datetime, end: datetime):
        rendered_query = self.render_query(start, end)
        logger.debug("executing time aggregation", extra={"query": rendered_query})
        return self._context.engine_adapter.fetchdf(rendered_query)

    def run_rolling(self, start: datetime, end: datetime):
        df: pd.DataFrame = pd.DataFrame()
        logger.debug(f"run_rolling called with start={start} and end={end}")
        count = 0
        for day in arrow.Arrow.range("day", arrow.get(start), arrow.get(end)):
            count += 1
            rendered_query = self.render_query(day.datetime, day.datetime)
            logger.debug(
                f"executing rolling window: {rendered_query}",
                extra={"query": rendered_query},
            )
            day_result = self._context.engine_adapter.fetchdf(rendered_query)
            df = pd.concat([df, day_result])

        return df

    def render_query(self, start: datetime, end: datetime) -> str:
        variables: t.Dict[str, t.Any] = {
            "start_ds": start.strftime("%Y-%m-%d"),
            "end_ds": end.strftime("%Y-%m-%d"),
        }
        logger.debug(f"start_ds={variables['start_ds']} end_ds={variables['end_ds']}")
        time_aggregation = self._ref.get("time_aggregation")
        rolling_window = self._ref.get("window")
        rolling_unit = self._ref.get("unit")
        if time_aggregation:
            variables["time_aggregation"] = time_aggregation
        if rolling_window and rolling_unit:
            variables["rolling_window"] = rolling_window
            variables["rolling_unit"] = rolling_unit
        variables.update(self._locals)
        additional_macros = create_unregistered_macro_registry(
            [
                metrics_end,
                metrics_start,
                metrics_sample_date,
            ]
        )
        evaluated_query = run_macro_evaluator(
            self._query,
            additional_macros=additional_macros,
            variables=variables,
            engine_adapter=self._context.engine_adapter,
            runtime_stage=RuntimeStage.EVALUATING,
        )
        rendered_parts = list(
            map(
                lambda a: a.sql(dialect=self._context.engine_adapter.dialect),
                evaluated_query,
            )
        )
        return "\n".join(rendered_parts)

    def commit(self, start: datetime, end: datetime, destination: str):
        """Like run but commits the result to the database"""
        try:
            result = self.run(start, end)
        except:
            logger.error(
                "Running query failed",
                extra={"query": self._query[0].sql(dialect="duckdb", pretty=True)},
            )
            raise

        create_table = generate_duckdb_create_table(result, destination)

        logger.debug("creating duckdb table")
        self._context.engine_adapter.execute(create_table)

        logger.debug("inserting results from the run")
        self._context.engine_adapter.insert_append(destination, result)
        return result
