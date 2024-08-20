# Dashboard Plugin

A plugin that enables users to construct custom dashboards that display
statistics of interest about the current dataset (and beyond).

https://github.com/user-attachments/assets/373a7cfe-aab7-45a2-a9f5-76775dcdfa72

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/dashboard
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

3.  Select the `Dashboard` panel

4.  Build a dashboard as shown in the video above!
