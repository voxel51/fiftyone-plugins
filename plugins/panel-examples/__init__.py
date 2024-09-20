"""
Example panels.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import os

import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone import ViewField as F
import random
import numpy as np

from bson import ObjectId


class CounterExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_counter",
            label="Examples: Counter",
        )

    def on_load(self, ctx):
        ctx.panel.state.my_count = 0

    def increment(self, ctx):
        ctx.panel.state.my_count += 1

    def decrement(self, ctx):
        ctx.panel.state.my_count -= 1

    def reset(self, ctx):
        ctx.panel.state.my_count = 0

    def say_hi(self, ctx):
        ctx.ops.notify("Hi!")

    def render(self, ctx):
        panel = types.Object()

        # Add menu to panel
        menu = panel.menu("menu", variant="square", color="51")
        menu.btn(
            "increment",
            icon="add",
            label="Increment",
            on_click=self.increment,
        )
        menu.btn(
            "decrement",
            icon="remove",
            label="Decrement",
            on_click=self.decrement,
        )
        menu.btn("reset", icon="360", label="Reset", on_click=self.reset)
        menu.btn(
            "say_hi",
            icon="emoji_people",
            label="Say hi!",
            variant="contained",
            color="white",
        )

        # Add counter info to panel
        panel.message("my_count", f"Count: {ctx.panel.state.my_count}")

        return types.Property(
            panel,
            view=types.GridView(
                align_y="center",
                align_x="center",
                orientation="vertical",
                height=100,
            ),
        )


class PlotExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_plot",
            label="Examples: Plot",
        )

    def on_load(self, ctx):
        # create data for a plotly heatmap
        ctx.panel.data.data = [
            {
                "z": [
                    [1, 20, 30],
                    [20, 1, 60],
                    [30, 60, 1],
                ],
                "type": "heatmap",
                "colorscale": "Viridis",
                "selectedpoints": [[0, 0]],
            }
        ]

    def on_click(self, ctx):
        z = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        x = ctx.params.get("x", 0)
        y = ctx.params.get("y", 0)
        z[y][x] = 1
        ctx.panel.set_data("data[0].z", z)

    def on_double_click(self, ctx):
        self.on_load(ctx)

    def render(self, ctx):
        panel = types.Object()

        # grab data field from state and render it in a plotly view
        panel.plot(
            "data",
            label="Plotly Panel",
            on_click=self.on_click,
            on_double_click=self.on_double_click,
        )  # shortcut for plot creation

        return types.Property(
            panel,
            view=types.GridView(align_x="center", orientation="vertical"),
        )


class MarkdownExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_markdown",
            label="Examples: Markdown",
        )

    def on_load(self, ctx):
        ctx.panel.state.title = "# Markdown Panel Title"
        ctx.panel.state.body = (
            "_The below code will be rendered via markdown in multiple ways._"
        )

    def render(self, ctx):
        panel = types.Object()

        # load markdown as a panel string type with MarkdownView
        panel.str(
            "title",
            # label="Markdown Title",
            # description="An example of rendering a markdown title as through the str method of the panel object.",
            view=types.MarkdownView(),
        )
        panel.str(
            "body",
            # label="Markdown Body",
            # description="An example of rendering the markdown body through the str method of the panel object.",
            view=types.MarkdownView(),
        )

        # load markdown as a pure string
        markdown_intro_message = "## What Can I Do?\n\nHere I can create: \n* Text\n* Format Fonts\n* _Italicize Things_\n* **Bold**\n"
        panel.md(markdown_intro_message, name="markdown1")

        # load markdown.md file from py-panel-example-2 folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        markdown_path = os.path.join(current_dir, "assets/markdown.md")

        with open(markdown_path, "r") as markdown_file:
            panel.md(markdown_file.read(), name="markdown2")

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )


class TableExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_table",
            label="Examples: Table",
        )

    def on_load(self, ctx):
        table = [
            {
                "Category": "Number",
                "a": "1",
                "b": "2",
                "c": "3",
                "d": "4",
                "e": "5",
                "f": "6",
                "g": "7",
                "h": "8",
                "i": "9",
                "j": "10",
                "k": "11",
                "l": "12",
                "m": "13",
                "n": "14",
            },
            {  # add a row
                "Category": "Letter",
                "a": "a",
                "b": "b",
                "c": "c",
                "d": "d",
                "e": "e",
                "f": "f",
                "g": "g",
                "h": "h",
                "i": "i",
                "j": "j",
                "k": "k",
                "l": "l",
                "m": "m",
                "n": "n",
            },
        ]

        ctx.panel.state.table = table
        ctx.panel.state.table_two = table

    def render(self, ctx):
        panel = types.Object()

        table = types.TableView()
        table.add_column("Category", label="")
        table.add_column("a", label="a")
        table.add_column("b", label="b")
        table.add_column("c", label="c")
        table.add_column("d", label="d")
        table.add_column("e", label="e")
        table.add_column("f", label="f")
        table.add_column("g", label="g")
        table.add_column("h", label="h")
        table.add_column("i", label="i")
        table.add_column("j", label="j")
        table.add_column("k", label="k")
        table.add_column("l", label="l")
        table.add_column("m", label="m")
        table.add_column("n", label="n")

        panel.list("table", types.Object(), view=table, label="Table Example")

        panel.list(
            "table_two", types.Object(), view=table, label="Table Example"
        )

        return types.Property(panel, view=types.ObjectView())


class MediaPlayerExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_media_player",
            label="Examples: Media Player",
        )

    def on_load(self, ctx):
        ctx.panel.state.media_player = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }

    def render(self, ctx):
        panel = types.Object()

        panel.md(
            "# Media View Player Example\n\n_Here's a fun video to check out_",
            name="intro_message",
        )

        media_player = types.MediaPlayerView()

        panel.obj(
            "media_player",
            view=media_player,
            label="Media Player Example",
            default={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )


class ImageExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_image",
            label="Examples: Image",
        )

    def on_load(self, ctx):
        # Load image from static URL
        ctx.panel.state.single_image = "https://static6.depositphotos.com/1119834/620/i/450/depositphotos_6201075-stock-photo-african-elephant-smelling.jpg"

        # Load 10 images from dataset
        samples = ctx.dataset.limit(10)
        for index, sample in enumerate(samples):
            image_path = (
                f"http://localhost:5151/media?filepath={sample.filepath}"
            )
            ctx.panel.set_state(f"image{index}", image_path)

    def render(self, ctx):
        panel = types.Object()

        panel.md(
            "# Image Collection\n\n_Here's a collage of images that can be loaded a few different ways_",
            name="intro_message",
        )

        panel.md(
            "## Single Image\n\n_This image was loaded from a url_",
            name="header_one",
        )
        image_holder = types.ImageView()

        panel.view(
            "single_image", view=image_holder, caption="A picture of a canyon"
        )

        panel.md("---", name="divider")
        panel.md(
            "## Multiple Images\n\n_All these images were loaded from our current dataset_",
            name="header_two",
        )

        for index in range(10):
            image_holder = types.ImageView()
            panel.view(
                f"image{index}", view=image_holder, caption=f"Image {index}"
            )

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )


class MultiviewExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_multiview",
            label="Examples: Multiview",
        )

    def on_load(self, ctx):
        ctx.panel.state.table = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 32},
        ]

        ctx.panel.state.code = "def main():\n\tprint('Hello World!')"
        ctx.panel.data.plot = [
            {
                "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "y": [2, 6, 3, 9, 5, 12, 7, 16, 8, 20],
                "type": "scatter",
                "mode": "lines+markers",
                "marker": {"color": "orange"},
            },
            {
                "type": "bar",
                "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "y": [2, 5, 3, 5, 8, 3, 15, 16, 8, 22],
                "marker": {"color": "lightblue"},
            },
        ]
        ctx.panel.state.plot_layout = {
            "width": 600,
            "height": 240,
            "title": "A Fancy Plot",
        }

    def render(self, ctx):
        panel = types.Object()

        # Table
        table = types.TableView()
        table.add_column("name", label="Name")
        table.add_column("age", label="Age")

        panel.obj("table", view=table)

        # Code
        code_snippet = types.CodeView(width=50, language="python")
        panel.view("code", view=code_snippet, label="Code Example")

        # Plot
        plot = types.PlotlyView(layout=ctx.panel.state.plot_layout)
        panel.obj("plot", view=plot, label="Multi-Plot Example")

        return types.Property(panel, view=types.GridView(gap=3))


class InputsExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_inputs",
            label="Examples: Inputs",
        )

    def on_load(self, ctx):
        max_images = 10
        ctx.panel.state.slider_value = 5

        samples = ctx.dataset.limit(max_images)
        for index, sample in enumerate(samples):
            image_path = (
                f"http://localhost:5151/media?filepath={sample.filepath}"
            )
            ctx.panel.set_state(f"image{index}", image_path)

    def reset_slider(self, ctx):
        ctx.panel.state.slider_value = 1

    def change_value(self, ctx):
        # Grab value from ctx.params
        ctx.panel.state.slider_value = (
            ctx.params["value"] or ctx.params["panel_state"]["slider_value"]
        )

    def render(self, ctx):
        panel = types.Object()

        # Load all images in state variable from dataset
        for index in range(ctx.panel.state.slider_value):
            image_holder = types.ImageView(width="200px")
            panel.view(
                f"image{index}", view=image_holder, caption=f"Image {index}"
            )

        # Slider
        schema = {"min": 0, "max": 10, "multipleOf": 1}
        slider = types.SliderView(
            data=ctx.panel.state.slider_value, label="Example Slider"
        )

        panel.int(
            "slider_value", view=slider, on_change=self.change_value, **schema
        )

        # Button
        panel.btn("reset", label="Reset Slider", on_click=self.reset_slider)

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )


class InteractivePlotExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_interactive_plot",
            label="Examples: Interactive Plot",
        )

    def on_load(self, ctx):
        # Get target field
        target_field = (
            ctx.panel.state.target_field or "ground_truth.detections.label"
        )
        ctx.panel.state.target_field = target_field

        # Compute target histogram for current dataset
        counts = ctx.dataset.count_values(target_field)
        keys, values = zip(*sorted(counts.items(), key=lambda x: x[0]))

        # Store as panel data for efficiency
        ctx.panel.data.histogram = {"x": keys, "y": values, "type": "bar"}

        # Launch panel in a horizontal split view
        ctx.ops.split_panel("example_interactive_plot", layout="horizontal")

    def on_change_view(self, ctx):
        # Update histogram when current view changes
        self.on_load(ctx)

    def on_histogram_click(self, ctx):
        # The histogram bar that the user clicked
        x = ctx.params.get("x")

        # Create a view that matches the selected histogram bar
        field = ctx.panel.state.target_field
        view = _make_matching_view(ctx.dataset, field, x)

        # Load view in App
        if view:
            ctx.ops.set_view(view)

    def reset(self, ctx):
        ctx.ops.clear_view()
        self.on_load(ctx)

    def render(self, ctx):
        panel = types.Object()

        panel.plot(
            "histogram",
            layout={
                "title": {
                    "text": "Interactive Histogram",
                    "xanchor": "center",
                    "yanchor": "top",
                    "automargin": True,
                },
                "xaxis": {"title": "Labels"},
                "yaxis": {"title": "Count"},
            },
            on_click=self.on_histogram_click,
            width=100,
        )

        panel.btn(
            "reset",
            label="Reset Chart",
            on_click=self.reset,
            variant="contained",
        )

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center",
                align_y="center",
                orientation="vertical",
                height=100,
                width=100,
                gap=2,
                padding=0,
            ),
        )


def _make_matching_view(dataset, field, value):
    if field.endswith(".label"):
        root_field = field.split(".")[0]
        return dataset.filter_labels(root_field, F("label") == value)
    elif field == "tags":
        return dataset.match_tags(value)
    else:
        return dataset.match(F(field) == value)


class DropdownMenuExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_dropdown_menu",
            label="Examples: Dropdown Menu",
        )

    def on_load(self, ctx):
        ctx.panel.state.selection = None

    def alter_selection(self, ctx):
        ctx.panel.state.selection = ctx.params["value"]

    def refresh_page(self, ctx):
        ctx.ops.reload_dataset()

    def reload_samples(self, ctx):
        ctx.ops.reload_samples()

    def say_hi(self, ctx):
        ctx.ops.notify("Hi!", variant="success")

    def render(self, ctx):
        panel = types.Object()

        panel.md(
            """
            ### Welcome to the Python Panel Dropdown Menu Example
            Use the menu below to select what you would like to do next!
            
            ---
            
        """,
            name="header",
            width=50,  # 50% of current panel width
            height="200px",
        )

        menu = panel.menu("menu", variant="square", color="secondary")

        # Define a dropdown menu and add choices
        dropdown = types.DropdownView()
        dropdown.add_choice(
            "refresh",
            label="Display Refresh Button",
            description="Displays button that will refresh the FiftyOne App",
        )
        dropdown.add_choice(
            "reload_samples",
            label="Display Reload Samples Button",
            description="Displays button that will reload the samples view",
        )
        dropdown.add_choice(
            "say_hi",
            label="Display Hi Button",
            description="Displays button that will say hi",
        )

        # Add dropdown menu to the panel as a view and use the `on_change`
        # callback to trigger `alter_selection`
        menu.str(
            "dropdown",
            view=dropdown,
            label="Dropdown Menu",
            on_change=self.alter_selection,
        )

        # Change panel visual state dependent on dropdown menu selection
        if ctx.panel.state.selection == "refresh":
            menu.btn(
                "refresh",
                label="Refresh FiftyOne",
                on_click=self.refresh_page,
                color="51",
            )
        elif ctx.panel.state.selection == "reload_samples":
            menu.btn(
                "reload_samples",
                label="Reload Samples",
                on_click=self.reload_samples,
                color="51",
            )
        elif ctx.panel.state.selection == "say_hi":
            menu.btn(
                "say_hi",
                label="Say Hi",
                on_click=self.say_hi,
                color="51",
            )

        return types.Property(
            panel,
            view=types.GridView(
                height=100,
                width=100,
                align_x="center",
                align_y="center",
                orientation="vertical",
            ),
        )


class WalkthroughExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_walkthrough",
            label="Examples: Walkthrough",
        )

    def on_load(self, ctx):
        ctx.panel.state.page = 1

        info_table = [
            {
                "Dataset Name": f"{ctx.dataset.name}",
                "Dataset Description": "FiftyOne Quick Start Zoo Dataset",
                "Number of Samples": f"{ctx.dataset.count()}",
            },
        ]

        ctx.panel.state.info_table = info_table

    def go_to_next_page(self, ctx):
        ctx.panel.state.page = ctx.panel.state.page + 1

    def go_to_previous_page(self, ctx):
        ctx.panel.state.page = ctx.panel.state.page - 1

    def reset_page(self, ctx):
        ctx.panel.state.page = 1

    def open_operator_io(self, ctx):
        ctx.ops.open_panel("OperatorIO")

    def render(self, ctx):
        panel = types.Object()

        # Define a vertical stack to live inside your panel
        stack = panel.v_stack(
            "welcome", gap=2, width=75, align_x="center", align_y="center"
        )
        button_container = types.GridView(
            gap=2, align_x="left", align_y="center"
        )

        page = ctx.panel.get_state("page", 1)

        if page == 1:
            stack.md(
                """
                ### A Tutorial Walkthrough

                Welcome to the FiftyOne App! Here is a great example of what it looks like to create a tutorial style walkthrough via a Python Panel.
            """,
                name="markdown_screen_1",
            )
            stack.media_player(
                "video",
                "https://youtu.be/ad79nYk2keg",
                align_x="center",
                align_y="center",
            )
        elif page == 2:
            stack.md(
                """
                ### Information About Your Dataset
                                
                Perhaps you would like to know some more information about your dataset?
            """,
                name="markdown_screen_2",
            )
            table = types.TableView()

            # set table columns
            table.add_column("Dataset Name", label="Dataset Name")
            table.add_column("Dataset Description", label="Description")
            table.add_column("Number of Samples", label="Number of Samples")

            panel.obj(
                name="info_table",
                view=table,
                label="Cool Info About Your Data",
            )
        elif page == 3:
            if ctx.panel.state.operator_status != "opened":
                stack.md(
                    """
                    ### One Last Trick
                                
                    If you want to do something cool, click the button below. 
                """,
                    name="markdown_screen_3",
                )
                btns = stack.obj("top_btns", view=button_container)
                btns.type.btn(
                    "open_operator_io",
                    label="Do Something Cool",
                    on_click=self.open_operator_io,
                    variant="contained",
                )
        else:
            stack.md(
                """
                #### How did you get here?
                Looks like you found the end of the walkthrough. Or have you gotten a little lost in the grid? No worries, let's get you back to the walkthrough!
            """
            )
            btns = stack.obj("btns", view=button_container)
            btns.type.btn("reset", label="Go Home", on_click=self.reset_page)

        # Arrow navigation to go to next or previous page
        panel.arrow_nav(
            "arrow_nav",
            forward=page != 3,  # hidden for the last page
            backward=page != 1,  # hidden for the first page
            on_forward=self.go_to_next_page,
            on_backward=self.go_to_previous_page,
        )

        return types.Property(
            panel,
            view=types.GridView(
                height=100, width=100, align_x="center", align_y="center"
            ),
        )


EXAMPLE_DATA = {
    "x": [random.randint(1, 100) for _ in range(50)],
    "y": [random.randint(1, 100) for _ in range(50)],
}


class MyAnimatedPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_animated_plot",
            label="Examples: Animated Plot",
            surfaces="modal",
        )

    def on_load(self, ctx):
        if not ctx.current_sample:
            return
        current_sample = ctx.dataset[ctx.current_sample]
        frames = ctx.dataset.match(
            F("_sample_id") == ObjectId(current_sample.sample_id)
        )

        counts = []
        for frame in frames:
            frame_detections = frame.detections
            counts.append(len(frame_detections.detections))
        #   counts = []
        #   for frame_idx in current_sample.frames:
        #     print(frame_idx)
        #     frame_info = current_sample.frames[frame_idx]
        #     frame_detections = frame_info.detections
        #     counts.append(len(frame_detections.detections))

        ctx.panel.state.plot = {
            "type": "bar",
            "y": counts,
            "x": list(range(len(counts))),
        }

    def on_change_current_sample(self, ctx):
        self.on_load(ctx)

    def render(self, ctx):
        panel = types.Object()
        # define a hidden view that handles loading frames
        panel.obj(
            "frame_data",
            timeline_id="something",
            hidden=True,
            view=types.FrameLoaderView(
                on_load_range=self.on_load_range, target="plot.selectedpoints"
            ),
        )
        # define a property that will be updated by the FrameLoader
        panel.plot("plot", on_click=self.on_click_plot, height=100, width=100)
        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )

    def on_load_range(self, ctx):
        # # this would be called by the FrameLoader via the timeline hooks
        # r = ctx.params.get("range", [0, 0])
        # rendered_frames = []
        # # build the animation
        # for i in range(0, 50):
        #   rendered_frames.append(self.render_frame(i))

        # # this sends the rendered frames to the panel
        # # which will be used by the FrameLoader to update the plot
        # ctx.panel.data.frame_data = {
        #   "frames": rendered_frames,
        #   "range": r # should be the range
        # }
        current_sample = ctx.dataset[ctx.current_sample]
        num_frames = 120  # TODO: fix me
        frame_data = []
        for i in range(0, num_frames):
            rendered_frame = self.render_frame(i)
            frame_data.append(rendered_frame)
        ctx.panel.data.frame_data = {
            "frames": frame_data,
            "range": [0, num_frames],
        }

    def on_click_plot(self, ctx):
        ctx.ops.notify(
            f"You clicked on the plot! x = {ctx.params.get('x')}",
            variant="info",
        )

    def render_frame(self, frame):
        # x = np.linspace(0, 10, 50)
        # y = np.sin(x + frame * 0.2)

        # x = x.tolist()
        # y = y.tolist()

        # plot = {
        #     "type": "bar",
        #     "x": x,
        #     "y": y,
        #     "selectedpoints": [frame % 50]
        # }

        return [frame]


class ImageOrderExample(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_image_order", label="Examples: Image Order"
        )

    def on_load(self, ctx):
        image_state = {}
        for index, sample in enumerate(ctx.dataset.limit(10)):
            image_path = (
                f"http://localhost:5151/media?filepath={sample.filepath}"
            )
            image_state[f"image{index}"] = image_path
        ctx.panel.state.images = image_state

    def render(self, ctx):
        panel = types.Object()
        dashboard_view = types.DashboardView(
            allow_remove=False,
            width=100,
            height=100,
        )
        images = types.Object()
        for key, value in ctx.panel.state.images.items():
            images.view(key, view=types.ImageView(width=300))

        panel.add_property(
            "images", types.Property(images, view=dashboard_view)
        )
        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )


def register(p):
    p.register(CounterExample)
    p.register(PlotExample)
    p.register(MarkdownExample)
    p.register(TableExample)
    p.register(MediaPlayerExample)
    p.register(ImageExample)
    p.register(MultiviewExample)
    p.register(InputsExample)
    p.register(InteractivePlotExample)
    p.register(DropdownMenuExample)
    p.register(WalkthroughExample)
    p.register(MyAnimatedPanel)
    p.register(ImageOrderExample)
