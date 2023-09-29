"""
A simple Python service that executes FiftyOne delegated operations.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import time

from fiftyone.operators.delegated import DelegatedOperationService


def run_delegated_operations():
    try:
        service = DelegatedOperationService()
        while True:
            service.execute_queued_operations(limit=1, log=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_delegated_operations()
