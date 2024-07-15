import clickhouse_connect
from contextlib import contextmanager
from typing import Optional
from dagster import (
    ConfigurableResource,
    resource,
)
from pydantic import Field
from ..constants import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD
from ..utils.common import ensure

"""
Note: This code is predominantly copied from the BigQueryResource
It simply returns a Clickhouse Connect Client
"""

class ClickhouseResource(ConfigurableResource):
    """Resource for interacting with Clickhouse.

    Examples:
        .. code-block:: python

            @asset
            def tables(clickhouse: ClickhouseResource):
                with clickhouse.get_client() as client:
                    client.query(...)

            defs = Definitions(
                assets=[tables],
                resources={
                    "clickhouse": ClickhouseResource()
                }
            )
    """

    host: Optional[str] = Field(
        default=None,
        description="Clickhouse host.",
    )

    user: Optional[str] = Field(
        default=None,
        description="Clickhouse username.",
    )

    password: Optional[str] = Field(
        default=None,
        description="Clickhouse password.",
    )

    @contextmanager
    def get_client(self):
        #Context manager to create a Clickhouse Client.
        host = ensure(self.host or CLICKHOUSE_HOST, "Missing CLICKHOUSE_HOST")
        username = ensure(self.user or CLICKHOUSE_USER, "Missing CLICKHOUSE_USER")
        password = ensure(self.password or CLICKHOUSE_PASSWORD, "Missing CLICKHOUSE_PASSWORD")
        client = clickhouse_connect.get_client(
            host=host, 
            username=username,
            password=password,
            secure=True
        )
        yield client

@resource(
    config_schema=ClickhouseResource.to_config_schema(),
    description="Dagster resource for connecting to Clickhouse.",
)
def clickhouse_resource(context):
    clickhouse_resource = ClickhouseResource.from_resource_context(context)
    with clickhouse_resource.get_client() as client:
        yield client
