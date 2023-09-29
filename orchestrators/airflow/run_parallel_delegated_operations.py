"""
Airflow DAG that executes FiftyOne delegated operations in parallel.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
# pylint: disable=import-error
import asyncio
import logging
import re
import traceback

from airflow.operators.python import task
from airflow.decorators import dag, task
from datetime import datetime, timedelta
from fiftyone.operators.delegated import DelegatedOperationService
from fiftyone.operators.executor import ExecutionRunState, ExecutionResult

logger = logging.getLogger(__name__)
svc = DelegatedOperationService()


# task ids cannot have special characters, they must be alphanumeric or underscored.
def clean_task_id(task_id):
    return re.sub(r'\W+', '_', task_id)


@dag(start_date=datetime(2023, 9, 1),
     schedule=timedelta(minutes=1),
     max_active_runs=1,
     tags=["cron", "fiftyone"],
     dag_id="run-parallel-operations")
def execute_in_parallel():
    # get all the queued operations
    queued_ops = svc.list_operations(run_state=ExecutionRunState.QUEUED)
    logger.info(f"found : {len(queued_ops)} queued operations, filtering out duplicate datasets")
    # iterate over the number of queued operations and create a new task to process each one
    # don't execute multiple dags with the same dataset_id, for concurrency reasons.
    # also consider not executing certain operations in parallel, if they are known to be
    # resource intensive or have other side effects. (downloading the same model, for example)

    # if more than one instance of this DAG is able to run (max_active_runs),
    # then also consider checking for currently running operations (ExecutionRunState.RUNNING)
    # dataset ids.
    max_parallel = 6
    logger.info(f"max parallel tasks: {max_parallel}")

    dataset_ids = set()

    # if more than one instance of this DAG is able to run (max_active_runs),
    # then also consider checking for currently running operations (ExecutionRunState.RUNNING)
    # dataset ids.
    for i, op in enumerate(queued_ops):
        dataset_id = op.dataset_id
        # only operate on one dataset at a time
        if dataset_id in dataset_ids:
            continue
        # max possible parallel operations
        if len(dataset_ids) >= max_parallel:
            break

        dataset_ids.add(dataset_id)
        dataset_name = f"{op.context.dataset_name}_" if op.context.dataset_name else ""
        task_name = f"{dataset_name}{op.operator}"
        task_id = clean_task_id(task_name)

        @task(task_id=task_id)
        def execute_operation(delegated_operation):
            try:
                execution_result = asyncio.run(svc._execute_operator(delegated_operation))
                svc.set_completed(doc_id=delegated_operation.id, result=execution_result)
            except Exception as e:
                result = ExecutionResult(error=traceback.format_exc())
                svc.set_failed(doc_id=delegated_operation.id, result=result)
                logger.error(f"failed to execute delegated operation: {delegated_operation.id}", exc_info=True)
                raise Exception(result.error)

        execute_operation(op)


execute_in_parallel()
