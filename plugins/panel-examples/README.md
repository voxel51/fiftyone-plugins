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

-   **Description:** A panel that showcases a clickable set of buttons that
    will increment and decrement an on screen numerical value
-   Shows example of:
    -   `btn` usage as a clickable object
    -   `message` usage as a standalone string
    -   `ops.notify` usage to create a dismissible alert
    -   `on_click` usage as an invoked action when an object (i.e., button) is
        clicked
    -   panel _state_ as a numerical value
    -   manipulation of panel _state_ to increase and decrease saved numerical
        value

### example_plot

-   **Description:** A panel that showcases the basics of creating a plot. A
    heatmap is the plot of choice for this example
-   Shows example of:
    -   `plot` usage as a built-in method of a panel object
    -   rendering plot `data` separately from the instantiation of a `plot`
        object
    -   structuring plot data

### example_markdown

-   **Description:** A panel that showcases how to write markdown natively
    embedded.
-   Shows example of:
    -   displaying native panel objects such as `str` in `Markdown` format
    -   `md` usage as a built-in method of a panel object
    -   loading markdown from a file and rendering it within a panel
    -   saving markdown formatted strings to state and loading then into a
        panel

### example_table

-   **Description:** A panel that showcases how to create a column & row table.
-   Shows example of:
    -   how to create a `TableView` object
    -   how to add columns to a table object
    -   usage of the built in `list` method of a panel object to display a
        table object
    -   savings list(s) of row data as a _state_ object

### example_media_player

-   **Description:** A panel that showcases how to load in multimedia video
    based data.
-   Shows example of:
    -   how to load a _url_ as the source for a `MediaPlayerView` object
    -   using built in Markdown `md` object to add a title and subtext to panel
    -   usage of the built in `obj` method of a panel object to load in a
        `MediaPlayerView`
    -   usage of the `default` parameter to define a source url for a media
        player
    -   usage of `GridView` as return type to center align panel objects (i.e.,
        media player & text)

### example_image

-   **Description:** A panel that showcases how to load in still image data.
-   Shows example of:
    -   how to display an image from an external url
    -   how to display image(s) from within your already loaded datasets
    -   using built in Markdown `md` object to add a title and subtext to panel
    -   usage of the built in `view` method of a panel object to load a url as
        an image
    -   set multiple _state_ variables at once through use of iteration
    -   recall multiple _state_ variables values through use of iteration

### example_multi_view

-   **Description:** A panel that showcases how to load in multiple views &
    objects into one panel.
-   Shows example of:
    -   `TableView`, `PlotView`, and `CodeView` in a singular panel
    -   define a specific `layout` object that can be loaded into a `PlotView`
        to alter the appearance of a plot
    -   using _state_ to define a string formatted in Python syntax
    -   usage of `GridView` as a return type with a defined `gap` to space out
        objects within a panel

### example_duplicated

-   **Description:** A panel that uses Python class inheritance to render the
    exact same components of another panel. Uses state variables to change data
    that is rendered by inherited components.
-   Shows example of:
    -   creates a panel class that inherits an existing panel class
    -   using _state_ to change and define the data used from an inherited
        panel
    -   calls the `super()` method within the `render` function to reuse
        already defined panel components of parent panel
    -   usage of `GridView` as a return type with a defined `gap` to space out
        objects within a panel

### example_inputs

-   **Description:** A panel that changes state dependent on the inputs of a
    user.
-   Shows example of:
    -   using the `ctx` variable to access sample data from the `datasets`
        object
    -   creating helper functions that are executed on state changes like
        `on_click` and `on_change` for a defined object
    -   usage of `SliderView` with defined `schema` to bound slider choice
        options
    -   how to access the new value of a state change on an object via
        `ctx.params`

### example_interactive_plot

-   **Description:** A panel that displays an interactive plot. In taking
    action on the plot (i.e., clicking a bar) the view of your dataset changes
    in response.
-   Shows example of:
    -   how to create a `histogram` chart type of `PlotlyView`
    -   how to create titles, subtitles, axis titles, and change layout details
        of a `PlotlyView`
    -   how to iterate through all samples in a dataset via the `ctx` variable
    -   how to access metadata about a dataset such as
        `ground_truth.detections` and the associated `label` of such metadata
    -   how to use built-in `fiftyone` methods on `dataset` samples (i.e.,
        `filter_labels`)
    -   how to natively change server state with the `ctx.trigger()` method
    -   changing a dataset view using a `ctx.trigger("set_view")` call
    -   how to format, serialize, and load new view data into `ctx`
    -   usage of a built in `ctx` operator that resets any manipulated views
        back to base state (i.e., `ctx.ops.clear_view()`)
    -   how to access the underlying value of an object that did not change
        state but was selected (i.e, a clicked bar on a histogram)
    -   defines two shadow functions of a panel class that get trigger on
        server change(s)
        -   `on_change_ctx`: a method that fires anytime the state of `ctx`
            changes
        -   `on_change_view`: a method that fires anytime a dataset view
            changes

### example_dropdown_menu

-   **Description:** A panel that showcases a dropdown menu of selectable
    options. Selecting an option from the dropdown menu will trigger
    functionality that can alter the panel state itself, perform an operator or
    auxiliary function, or change the state of the running `fiftyone` instance.
-   Shows example of:
    -   how to use the `DropdownView` component
    -   how to add selectable choices to a dropdown menu
    -   how to capture the value selected from a `DropdownView` choice
    -   how to trigger a callback on the change or selection of a choice in a
        dropdown menu
    -   how to adjust the layout of a markdown rendering independent of the
        panel layout
    -   how to use if/else statements to show/hide objects from view within a
        panel

### example_walkthrough_tutorial

-   **Description:** A panel that imitates the ability to create a step-by-step
    tutorial style walkthrough via a panel.
-   Shows example of:
    -   how to utilize a `v_stack()` (i.e.,vertical stack view) within a panel
    -   how to create style buttons with CSS formatted code
    -   how to launch existing panels within a panel using the
        `ctx.ops.open_panel()` function
    -   how to retrieve metadata from your sample dataset via the `ctx`
        variable
    -   how to create a container within a panel to holder the formatting of
        sub-objects like buttons
    -   how to position components _relative_ and _absolute_ to one another
