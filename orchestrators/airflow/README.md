# Apache Airflow execution

The [`run_delegated_operations.py`](run_delegated_operations.py) file contains
a DAG that you can deploy to your [Apache Airflow](https://airflow.apache.org)
cluster that will execute all FiftyOne delegated operations for a connected
FiftyOne deployment.

The [`run_parallel_delegated_operations.py`](run_parallel_delegated_operations.py) file contains
a DAG that you can deploy to your [Apache Airflow](https://airflow.apache.org)
cluster that will execute FiftyOne delegated operations in parallel, accounting for concurrency issues by 
filtering out delegated operations that operate on the same dataset.

**Note:** FiftyOne Teams customers need to configure the execution environment
with the variables and plugin sources outlined in
[the documentation](https://docs.voxel51.com/teams/teams_plugins.html#setting-up-an-orchestrator).dd or 
