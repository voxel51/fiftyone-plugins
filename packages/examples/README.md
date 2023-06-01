## About

This plugin contains various example Python operators. Use these as a starting point for your
own operators, or read the source to understand how to:

 - use the operator type system
 - show messages to the user
 - create basic and interactive forms
 - create a progress bar
 - interact with FiftyOne `Views` and `Datasets`
 - update `Sample` fields

## Installation

CLI

```shell
fiftyone plugins download \
        https://github.com/voxel51/fiftyone-plugins \
        --plugin-names @voxel51/examples
```

Python

```python
import fiftyone.plugins as fop

fop.download_plugin(
    "https://github.com/voxel51/fiftyone-plugins",
    plugin_names=["@voxel51/examples"]
```

## Operators

### example_messages

 - Shows a `types.Notice`, `types.Warning` or `types.Error` to the user

### example_simple_input

 - Example of a single input and output allowing the user to provide a string value
 - The value provided is returned and displayed to the user
### example_choices

 - Example of a dynamic operator where the input can be resolved based on the `ctx.params`
 - Shows how to use `types.RadioGroup` and `types.Dropdown` to display choices to the user
### example_input_list

 - Example of providing a dynamic list for the user to provide and or edit
### example_image

 - Example of how to output images to the user
### example_table

 - Example of how to show a table to the user as output
### example_plot

 - Example of showing a plot as output
### example_output_styles

 - Example of the various ways you can present output to the user
### example_progress

 - Shows a full implementation of a progress bar
 - Example of a streaming operator
### example_set_field

 - Example of how to update a Sample
### example_settings

 - Example of reading all plugin settings
### example_markdown

 - Example rendering markdown as output