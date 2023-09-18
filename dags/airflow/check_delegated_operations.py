from airflow import DAG
from airflow.operators.python import PythonOperator

from fiftyone.operators.delegated import DelegatedOperationService

# define a graph to tell airflow how to execute the related tasks
# the edges are added at the end of this file
dag = DAG(
    dag_id="fiftyone-check-delegated-operations",
    schedule_interval="@continuous",
    max_active_runs=1,
    default_args={
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
        "provide_context": True,
    },
    description="A simple fiftyone DAG to check for & run delegated operations",
    catchup=False,
    tags=["cron", "fiftyone"]
)


def load_runs(ti, **context):
    DelegatedOperationService().execute_queued_operations(limit=1)


load_runs_task = PythonOperator(task_id="load_runs", python_callable=load_runs, provide_context=True, dag=dag)
