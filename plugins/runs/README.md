# Runs Plugin

A plugin that contains utilities for working with
[custom runs](https://docs.voxel51.com/plugins/developing_plugins.html#storing-custom-runs).

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/runs
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Usage

1.  Launch the App:

```py
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")
session = fo.launch_app(dataset)
```

2.  Press `` ` `` or click the `Browse operations` action to open the Operators
    list

3.  Select any of the operators listed below!

## Operators

### get_run_info

You can use this operator to get information about runs.

This operator is essentially a wrapper around
[get_run_info()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.get_run_info):

```py
info = dataset_or_view.get_run_info(run_key)
print(info)
```

### load_run_view

You can use this operator to load the view on which a run was performed.

This operator is essentially a wrapper around
[load_run_view()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.load_run_view):

```py
view = dataset.load_run_view(run_key)
```

### rename_run

You can use this operator to rename runs.

This operator is essentially a wrapper around
[rename_run()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.rename_run):

```py
dataset_or_view.rename_run_run(run_key, new_run_key)
```

### delete_run

You can use this operator to delete runs.

This operator is essentially a wrapper around
[delete_run()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.delete_run):

```py
dataset_or_view.delete_run(run_key)
```
