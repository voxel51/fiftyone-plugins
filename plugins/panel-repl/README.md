# Custom Dashboard Plugin

A plugin that enables custom dashboards in the FiftyOne app.

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

dataset = foz.load_zoo_dataset("quickstart")
session = fo.launch_app(dataset)
```

2.  Press the `+` button next to the "Samples" tab

3.  Click on "Custom Dashboard"

4. TBD
