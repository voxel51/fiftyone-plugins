# Apache Airflow execution

You can connect your [Apache Airflow](https://airflow.apache.org) cluster to
your FiftyOne or [FiftyOne Teams](https://docs.voxel51.com/teams/index.html)
deployment to run your
[delegated operations](https://docs.voxel51.com/plugins/using_plugins.html#delegated-operations).

## Serial execution

The [`run_delegated_operations.py`](run_delegated_operations.py) file contains
a DAG that you can deploy to your Airflow cluster that will serially execute
all delegated operations for a connected FiftyOne deployment.

## Parallel execution

The
[`run_parallel_delegated_operations.py`](run_parallel_delegated_operations.py)
file contains a DAG that you can deploy to your Airflow cluster that will
execute delegated operations in parallel.

Out of the box, Airflow uses a
[`SequentialExecutor`](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/sequential.html),
which will run only one task insance at a time. To run operations in parallel,
you will need to configure Airflow to use a different executor. The
[`CeleryExecutor`](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html)
is a recommended executor for running production operations in parallel.

## FiftyOne Teams Notes

[FiftyOne Teams](https://docs.voxel51.com/teams/index.html) customers need to
configure the execution environment with the variables and plugin sources
outlined in
[the docs](https://docs.voxel51.com/teams/teams_plugins.html#setting-up-an-orchestrator).
