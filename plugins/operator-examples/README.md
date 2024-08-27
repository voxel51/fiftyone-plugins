## Operator Examples

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
    --plugin-names @voxel51/operator-examples
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Basic structure

Python operators are built using this basic structure:

```python
import fiftyone.operators as foo


class ExampleOperator(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_operator",
            label="Examples: Operator",
        )

    def resolve_input(self, ctx):
        pass

    def execute(self, ctx):
        pass

    def resolve_output(self, ctx):
        pass


def register(p):
    p.register(ExampleOperator)
```

[Refer to the docs](https://docs.voxel51.com/plugins/developing_plugins.html#developing-operators)
for more details on how each method works and how to implement them.

## Example operators

Below are a list of operators that are included in this plugin. Each operator
is defined in `__init__.py`.

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

-   Example of reading plugin settings

### example_markdown

-   Example rendering markdown as output

### example_custom_view

-   Example of defining a custom `types.View()`

### example_open_histograms_panel

-   Example of placing a custom button in the App's action row that opens a
    panel

### example_selected_labels

-   Example of interacting with the currently selected labels in the App

### example_selected_samples

-   Example of interacting with the currently selected samples in the App

### example_current_sample

-   Example of interacting with the current sample in the App's modal

### example_set_view

-   Example of programmatically setting the App's current view

### example_delegated

-   Example of scheduling a delegated operation

### example_secrets

-   Example of accessing plugin secrets within an operator

### example_file_dropzone

-   Example of reading a user-uploaded file from a dropzone

### example_target_view

-   Example of using the builtin `ctx.target_view()` method

### example_lazy_field

-   Example of using the `types.LazyFieldView()` type

### example_python_view

-   Example of programmatically loading a view in the App by typing the
    corresponding Python as a string
