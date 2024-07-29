## Python Panel Examples

This directory contains various examples of how to creat objects, views, use
operators, and manipulate context state with Python Panels. Use these as a
starting point for building your own panels, or read the source to understand
how to:

-   create a basic python panel
-   use the panel type system
-   create, show, and manipulate basic object types (images, media players,
    strings, etc.)
-   create basic and interactive plots
-   use state functions
-   interact with FiftyOne datasets and views from within panels
-   create reusable templates from your panels

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/panel-examples
```

## Basic Structure

Most python panels are built using this general basic structure:

```python
import fiftyone.operators as foo


class ExamplePanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_panel", label="Example Python Panel"
        )

    def on_load(ctx: ExecutionContext):
        pass

    def render(self, ctx: ExecutionContext):
        pass


def register(p):
    p.register(ExamplePanel)
```

For further details on how each individual function works and how to use them,
please visit our [docs](https://docs.voxel51.com/plugins/index.html).

## Panels

Below are a list of panels that have been created to showcase the power of
Python Panels and some best practices on how to build them. Each panel is
defined as an example in `__init__.py`.

### example_counter

-   ...

### example_plot

-   ...

### example_markdown

-   ...

### example_table

-   ...

### example_media_player

-   ...

### example_image

-   ...

### example_multi_view

-   ...

### example_duplicated

-   ...

### example_inputs

-   ...

### example_interactive_plot

-   ...
