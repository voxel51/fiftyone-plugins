## Python View Plugin

This plugin contains a `create_view_with_python` operator that allows you to
load a view into your current dataset in the FiftyOne App by typing the
corresponding Python definition.

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/python-view
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Operators

### create_view_with_python

-   accepts Python as the only input param
-   the provided Python must start with "view."
-   updates the App's view to match the provided Python
