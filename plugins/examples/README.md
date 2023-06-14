## Examples

This plugin contains various example Python operators. Use these as a starting
point for your own operators, or read the source to understand how to:

-   use the operator type system
-   show messages to the user
-   create basic and interactive forms
-   create a progress bar
-   interact with FiftyOne datasets and views from within operators

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/examples
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Operators

### example_messages

-   Shows a `types.Notice`, `types.Warning` or `types.Error` to the user

### example_simple_input

-   Example of a single input and output allowing the user to provide a string
    value
-   The value provided is returned and displayed to the user

### example_choices

-   Example of a dynamic operator where the input can be resolved based on the
    `ctx.params`
-   Shows how to use `types.RadioGroup` and `types.Dropdown` to display choices
    to the user

### example_input_list

-   Example of providing a dynamic list for the user to provide and or edit

### example_image

-   Example of how to output images to the user

### example_table

-   Example of how to show a table to the user as output

### example_plot

-   Example of showing a plot as output

### example_output_styles

-   Example of the various ways you can present output to the user

### example_progress

-   Shows a full implementation of a progress bar
-   Example of a streaming operator

### example_set_field

-   Example of how to update a Sample

### example_settings

-   Example of reading all plugin settings

### example_markdown

-   Example rendering markdown as output
