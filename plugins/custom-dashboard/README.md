# Dashboard Plugin

A plugin that enables dashboards of user defined plots in the FiftyOne app.

https://github.com/voxel51/fiftyone-plugins/assets/25985824/7a8186fb-636f-4f7d-9ac7-8822a76cfded

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/dashboard-builder
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Usage

1.  Launch the App:

```py
import fiftyone as fo
import fiftyone.zoo as foz
import fiftyone.utils.random as four

dataset = foz.load_zoo_dataset("quickstart")
dataset.untag_samples("validation")

four.random_split(dataset, {"train": 0.6, "test": 0.3, "val": 0.1})
session = fo.launch_app(dataset)
```

2.  Press the `+` button next to the "Samples" tab

3.  Click on "Dashboard"

4.  Build a dashboard as shown in the video above
