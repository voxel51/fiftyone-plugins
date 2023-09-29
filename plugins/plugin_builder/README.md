## Plugin Builder Plugin

This plugin is a Python plugin that allows you to point and click your way to
custom plugin components. As you select options, the plugin will generate the
Python code for you. You can then copy and paste the code into a Python file
and use it as a starting point for your own custom plugin.

It demonstrates how to do the following:

-   Request the same input from the user in multiple form factors
-   Dynamically update code based on user input

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/plugin_builder
```

## Operators

### `build_component`

-   This operator walks you through the process of choosing a component type
    for a given type of input, and selecting the component's properties.

It currently supports the following component types:

1. `radio groups`: A way of selecting one of a set of mutually exclusive
   options
2. `booleans`: A way of selecting a true/false value
3. `floats`: A way of selecting a floating point number
4. `message`: A way of displaying a message to the user

Each of these component types has a set of properties that can be configured.

### `build_operator_skeleton`

-   This operator walks you through the process of creating an operator. It
    then generates a skeleton of the code for the operator.
-   Pressing the `Execute` button will add the plugin in the location of your
    choice!

## Usage

To use this plugin, press the "\'" key in the App and select the relevant
operator from the list. As you select options, the code block and the code
preview will be updated!
