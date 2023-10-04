# Apache Airflow execution

The [`run_delegated_operations.py`](run_delegated_operations.py) file contains
a DAG that you can deploy to your [Apache Airflow](https://airflow.apache.org)
cluster that will execute all FiftyOne delegated operations for a connected
FiftyOne deployment.

**Note:** FiftyOne Teams customers need to configure the execution environment
with the variables and plugin sources outlined in
[the documentation](https://docs.voxel51.com/teams/teams_plugins.html#setting-up-an-orchestrator).
