## About

This plugin contains an example of using both Python and JS together in a FiftyOne plugin.

It demonstrates how to do the following:

 - use Python and JS in the same plugin
 - define a `Panel`
 - adhoc operator execution
 - hook based operator execution
 - how to use the `build` package to build a JS plugin

## Installalation

CLI

```shell
fiftyone plugins download \
        https://github.com/voxel51/fiftyone-plugins \
        --plugin-names @voxel51/hello-world
```

Python

```python
import fiftyone.plugins as fop

fop.download_plugin(
    "https://github.com/voxel51/fiftyone-plugins",
    plugin_names=["@voxel51/hello-world"]
```

## Operators

### my_alert_operator

 - Example of a very basic JS operator

### count

 - Example of a simple python operator
 - Returns the size of the current view