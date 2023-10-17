# Plugin Management & Development

A plugin that contains utilities for managing your FiftyOne plugins and
building new plugins.

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/plugins
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

### install_plugin

You can use this operator to install FiftyOne plugins from within the App.

This operator is essentially a wrapper around the
[plugin installation methods](https://docs.voxel51.com/plugins/using_plugins.html#id2):

```py
import fiftyone.plugins as fop

# Plugin installation
fop.download_plugin(...)
```

where the operator's form allows you to choose between the following options:

-   Specify any GitHub URL that contains plugin(s) to install
-   Choose from any plugin listed in the
    [FiftyOne Plugins README](https://github.com/voxel51/fiftyone-plugins) to
    install

### manage_plugins

You can use this operator to manage your FiftyOne plugins from within the App.

This operator is essentially a wrapper around the following
[plugin methods](https://docs.voxel51.com/plugins/using_plugins.html#managing-plugins):

```py
import fiftyone.plugins as fop

# Plugin enablement
fop.list_plugins()
fop.enable_plugin(name)
fop.disable_plugin(name)

# Plugin package requirements
fop.load_plugin_requirements(name)
fop.ensure_plugin_requirements(name)
```

where the operator's form allows you to navigate between the available actions.

### build_component

![plugin_builder_component](https://github.com/voxel51/fiftyone-plugins/assets/12500356/19f1af29-7642-4b13-8317-01ba2a263e03)

This operator walks you through the process of choosing a component type for a
given type of input, and selecting the component's properties.

It currently supports the following component types:

1. `radio groups`: A way of selecting one of a set of mutually exclusive
   options
2. `booleans`: A way of selecting a true/false value
3. `floats`: A way of selecting a floating point number
4. `message`: A way of displaying a message to the user

Each of these component types has a set of properties that can be configured.

### build_operator_skeleton

![build_operator](https://github.com/voxel51/fiftyone-plugins/assets/12500356/436f17fa-acc7-4b7f-aa2e-d8edffc76c2e)

This operator walks you through the process of creating an operator. It then
generates a skeleton of the code for the operator.

Pressing the `Execute` button will add the plugin in the location of your
choice!
