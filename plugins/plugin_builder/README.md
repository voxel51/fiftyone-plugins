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
fiftyone plugins download https://github.com/jacobmarks/plugin-builder-plugin
```

## Operators

### `build_a_plugin`

-   This operator walks you through the process of choosing a component type
    for a given type of input, and selecting the component's properties.

It currently supports the following component types:

1. `radio groups`: A way of selecting one of a set of mutually exclusive
   options
2. `booleans`: A way of selecting a true/false value
3. `floats`: A way of selecting a floating point number
4. `message`: A way of displaying a message to the user

Each of these component types has a set of properties that can be configured.

## Usage

To use this plugin, press the "\'" key in the App and select the
`build_a_plugin` operator. You will be prompted to select a component type.
After selecting a component type, you will be prompted to select the
component's properties. As you do so, the code block and the code preview will
be updated!