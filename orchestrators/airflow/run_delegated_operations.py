"""
Airflow DAG that executes FiftyOne delegated operations.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
# pylint: disable=import-error
from airflow import DAG
from airflow.operators.python import PythonOperator

from fiftyone.operators.delegated import DelegatedOperationService


dag = DAG(
    dag_id="fiftyone-run-delegated-operations",
    schedule_interval="@continuous",
    max_active_runs=1,
    default_args={
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
        "provide_context": True,
    },
    description="A DAG that executes FiftyOne delegated operations",
    catchup=False,
    tags=["cron", "fiftyone"],
)


def execute_next_queued_operation(ti, **context):
    service = DelegatedOperationService()
    service.execute_queued_operations(limit=1)


task = PythonOperator(
    task_id="execute_next_queued_operation",
    python_callable=execute_next_queued_operation,
    provide_context=True,
    dag=dag,
)
