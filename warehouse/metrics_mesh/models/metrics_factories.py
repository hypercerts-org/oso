import os

from metrics_tools.factory import MetricQueryDef, RollingConfig, timeseries_metrics

timeseries_metrics(
    start=os.environ.get("SQLMESH_TIMESERIES_METRICS_START", "2015-01-01"),
    catalog="metrics",
    model_prefix="timeseries",
    timeseries_sources=[
        "events_daily_to_artifact",
        "events_daily_to_artifact_with_lag",
        "issue_event_time_deltas",
        "first_of_event_from_artifact",
    ],
    metric_queries={
        # This will automatically generate star counts for the given roll up periods.
        # A time_aggregation is just a simple addition of the aggregation. So basically we
        # calculate the daily time_aggregation every day by getting the count of the day.
        # Then the weekly every week by getting the count of the week and
        # monthly by getting the count of the month.
        # Additionally this will also create this along the dimensions (entity_types) of
        # project/collection so the resulting models will be named as follows
        # `metrics.timeseries_stars_to_{entity_type}_{time_aggregation}`
        "stars": MetricQueryDef(
            ref="stars.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "commits": MetricQueryDef(
            ref="commits.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "comments": MetricQueryDef(
            ref="comments.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "releases": MetricQueryDef(
            ref="releases.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "forks": MetricQueryDef(
            ref="forks.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "repositories": MetricQueryDef(
            ref="repositories.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "active_contracts": MetricQueryDef(
            ref="active_contracts.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "contributors": MetricQueryDef(
            ref="contributors.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "active_developers": MetricQueryDef(
            ref="active_developers.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        # This defines something with a rolling option that allows you to look back
        # to some arbitrary window. So you specify the window and specify the unit.
        # The unit and the window are used to pass in variables to the query. So it's
        # up to the query to actually query the correct window.
        # The resultant models are named as such
        # `metrics.timeseries_active_days_to_{entity_type}_over_{window}_{unit}`
        "developer_active_days": MetricQueryDef(
            ref="active_days.sql",
            vars={
                "activity_event_types": ["COMMIT_CODE"],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",  # This determines how often this is calculated
            ),
            entity_types=["artifact", "project", "collection"],
            is_intermediate=True,
        ),
        "contributor_active_days": MetricQueryDef(
            ref="active_days.sql",
            vars={
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                    "PULL_REQUEST_MERGED",
                ],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",  # This determines how often this is calculated
            ),
            entity_types=["artifact", "project", "collection"],
            is_intermediate=True,
        ),
        "developer_classifications": MetricQueryDef(
            ref="developer_activity_classification.sql",
            vars={
                "full_time_ratio": 10 / 30,
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
        ),
        "contributor_classifications": MetricQueryDef(
            ref="contributor_activity_classification.sql",
            vars={
                "full_time_ratio": 10 / 30,
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                    "PULL_REQUEST_MERGED",
                ],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
        ),
        # Currently this query performs really poorly. We need to do some debugging on it
        # "user_retention_classifications": MetricQueryDef(
        #     ref="user_retention_classification.sql",
        #     vars={
        #         "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
        #     },
        #     rolling=RollingConfig(
        #         windows=[30, 90, 180],
        #         unit="day",
        #         cron="@daily",
        #     ),
        #     entity_types=["artifact", "project", "collection"],
        # ),
        "change_in_developer_activity": MetricQueryDef(
            ref="change_in_developers.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
        ),
        "commits_rolling": MetricQueryDef(
            ref="commits.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "opened_pull_requests": MetricQueryDef(
            ref="prs_opened.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "merged_pull_requests": MetricQueryDef(
            ref="prs_merged.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "opened_issues": MetricQueryDef(
            ref="issues_opened.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "closed_issues": MetricQueryDef(
            ref="issues_closed.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "avg_prs_time_to_merge": MetricQueryDef(
            ref="prs_time_to_merge.sql",
            rolling=RollingConfig(
                windows=[90, 180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "avg_time_to_first_response": MetricQueryDef(
            ref="time_to_first_response.sql",
            rolling=RollingConfig(
                windows=[90, 180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "active_addresses_aggregation": MetricQueryDef(
            ref="active_addresses.sql",
            vars={
                "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
            },
            time_aggregations=["daily", "monthly"],
        ),
        "active_addresses_rolling": MetricQueryDef(
            ref="active_addresses.sql",
            vars={
                "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
        ),
        "gas_fees": MetricQueryDef(
            ref="gas_fees.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "transactions": MetricQueryDef(
            ref="transactions.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "contributors_lifecycle": MetricQueryDef(
            ref="lifecycle.sql",
            vars={
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                    "PULL_REQUEST_MERGED",
                ],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        # "libin": MetricQueryDef(
        #     ref="libin.sql",
        #     vars={
        #         "activity_event_types": [
        #             "COMMIT_CODE",
        #             "ISSUE_OPENED",
        #             "PULL_REQUEST_OPENED",
        #             "PULL_REQUEST_MERGED",
        #         ],
        #     },
        #     rolling=RollingConfig(
        #         windows=[30, 90, 180],
        #         unit="day",
        #         cron="@daily",
        #     ),
        #     entity_types=["artifact"],
        # ),
        "funding_received": MetricQueryDef(
            ref="funding_received.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "dependencies": MetricQueryDef(
            ref="dependencies.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
        ),
    },
    default_dialect="clickhouse",
)
