# Local execution

Open source users can launch a service that will execute all delegated
operations locally via the following
[CLI command](https://docs.voxel51.com/cli/index.html#cli-fiftyone-delegated-launch):

```shell
fiftyone delegated launch
```

The above command is effectively syntax sugar for running the
[`run_delegated_operations.py`](run_delegated_operations.py) script:

```shell
python run_delegated_operations.py
```

Note: For FiftyOne Teams customers, you will still need to configure the execution environment with the varaibles and plugin sources outlined in [the documentation](https://docs.voxel51.com/teams/teams_plugins.html#setting-up-an-orchestrator).
