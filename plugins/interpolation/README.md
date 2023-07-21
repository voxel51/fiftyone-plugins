## Hello World

This plugin contains an example of using both Python and JS together in a
FiftyOne plugin.

It demonstrates how to do the following:

-   use Python and JS in the same plugin
-   define a `Panel`
-   ad hoc operator execution
-   hook-based operator execution
-   how to use the `build` package to build a JS plugin

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/hello-world
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Operators

### my_alert_operator

-   example of a very basic JS operator

### count

-   example of a simple python operator
-   returns the size of the current view
