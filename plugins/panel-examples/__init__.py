import json
import os

from bson import json_util

import fiftyone.operators as foo
import fiftyone.operators.types as types

from fiftyone import ViewField as F
from fiftyone.operators.executor import ExecutionContext


###
# Counter
###


class CounterPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_counter", label="Python Panel Example: Counter"
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        ctx.panel.state.my_count = 0

    def increment(self, ctx: ExecutionContext):
        ctx.panel.state.my_count += 1

    def decrement(self, ctx: ExecutionContext):
        ctx.panel.state.my_count -= 1

    def reset(self, ctx: ExecutionContext):
        ctx.panel.state.my_count = 0

    def say_hi(self, ctx: ExecutionContext):
        ctx.ops.notify("Hi!")

    def render(self, ctx: ExecutionContext):
        panel = types.Object()
        panel.message("my_count", f"Count: {ctx.panel.state.my_count}")
        panel.btn(
            "increment", icon="add", label="Increment", on_click=self.increment
        )
        panel.btn(
            "decrement",
            icon="remove",
            label="Decrement",
            on_click=self.decrement,
        )
        panel.btn("reset", icon="360", label="Reset", on_click=self.reset)
        panel.btn(
            "say_hi",
            icon="emoji_people",
            label="Say hi!",
            on_click=self.say_hi,
            variant="contained",
        )
        return types.Property(
            panel,
            view=types.GridView(
                align_y="center", align_x="center", orientation="vertical"
            ),
        )


###
# Plot
###


class PlotPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_plot", label="Python Panel Example: Plot"
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        # set plot data with object
        plot_data = {
            "z": [
                [1, None, 30, 50, 1],
                [20, 1, 60, 80, 30],
                [30, 60, 1, -10, 20],
            ],
            "x": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
            ],
            "y": ["Morning", "Afternoon", "Evening"],
            "type": "heatmap",
            "hoverongaps": False,
        }

        ctx.panel.state.data = plot_data

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        # grab data field from state and render it in a plotly view
        panel.plot("data", label="Plotly Panel")  # shortcut for panel creation

        panel.obj("data", view=types.PlotlyView())

        return types.Property(
            panel,
            view=types.GridView(align_x="center", orientation="vertical"),
        )


###
# Markdown
###


class MarkdownPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_markdown", label="Python Panel Example: Markdown"
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        ctx.panel.state.title = "# Markdown Panel Title"
        ctx.panel.state.body = (
            "_The below code will be rendered via markdown in multiple ways._"
        )

    @staticmethod
    def render(ctx: ExecutionContext):
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


###
# Table
###


class TablePanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_table", label="Python Panel Example: Table"
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        # set table data with array of object

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

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        table = types.TableView()

        # set table columns
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

        # duplicate table for a second time with a new name to see multiple tables at once
        panel.list(
            "table_two", types.Object(), view=table, label="Table Example"
        )

        return types.Property(panel, view=types.ObjectView())


###
# Media Player
###


class MediaPlayerPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_media_player",
            label="Python Panel Example: Media Player",
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        ctx.panel.state.media_player = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }

    def render(self, ctx: ExecutionContext):
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


###
# Images
###


class ImagePanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_image", label="Python Panel Example: Image"
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        # filter 10 images from data set and set it to a state variable

        ctx.panel.state.single_image = "https://static6.depositphotos.com/1119834/620/i/450/depositphotos_6201075-stock-photo-african-elephant-smelling.jpg"

        samples = ctx.dataset.limit(10)
        for index, sample in enumerate(samples):
            image_path = (
                f"http://localhost:5151/media?filepath={sample.filepath}"
            )
            ctx.panel.set_state(f"image{index}", image_path)

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        panel.md(
            "# Image Collection\n\n_Here's a collage of images that can be loaded a few different ways_",
            name="intro_message",
        )

        # loading a single image from an url
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

        # load all images in state variable from dataset
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


###
# Multiple Views
###


class MultiViewPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_multi_view",
            label="Python Panel Example: Multiple Views",
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        ctx.panel.state.table = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 32},
        ]

        ctx.panel.state.code = "def main():\n\tprint('Hello World!')"
        ctx.panel.state.plot = [
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

    def render(self, ctx: ExecutionContext):
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

        return types.Property(
            panel, view=types.GridView(gap=3)
        )  # anything within GridView can take height and width


###
# Templating (Inheritance)
###


class DuplicatedPanel(MultiViewPanel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_duplicated",
            label="Python Panel Example: Templating (Inheritance)",
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        # change state of objects already named in MultiViewPanel
        ctx.panel.state.table = [
            {"name": "Billy", "age": 23},
            {"name": "Joel", "age": 64},
        ]

        ctx.panel.state.code = "def main():\n\tchanged_message = 'I am duplicate!'\n\tprint(changed_message)"
        ctx.panel.state.plot = [
            {
                "values": [19, 26, 55],
                "labels": ["Residential", "Non-Residential", "Utility"],
                "type": "pie",
            }
        ]
        ctx.panel.state.plot_layout = {
            "width": 250,
            "height": 250,
            "title": "A Pie Chart",
        }

    def render(self, ctx: ExecutionContext):
        # inherit from MultiViewPanel
        return super().render(ctx)


###
# Inputs
###


class InputMutationsPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_inputs",
            label="Python Panel Example: Input Mutations",
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):
        max_images = 10
        ctx.panel.state.slider_value = 5

        samples = ctx.dataset.limit(max_images)
        for index, sample in enumerate(samples):
            image_path = (
                f"http://localhost:5151/media?filepath={sample.filepath}"
            )
            ctx.panel.set_state(f"image{index}", image_path)

    def reset_slider(self, ctx: ExecutionContext):
        ctx.panel.state.slider_value = 1

    def change_value(self, ctx: ExecutionContext):
        # grab value from ctx.params
        ctx.panel.state.slider_value = (
            ctx.params["value"] or ctx.params["panel_state"]["slider_value"]
        )

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        # load all images in state variable from dataset
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


###
# Interactive Plot
###


class InteractivePlot(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="example_interactive_plot",
            label="Python Panel Example: Interactive Plot",
        )

    @staticmethod
    def on_load(ctx: ExecutionContext):

        # tabulate histogram values
        label_counts = {}
        for sample in ctx.dataset.iter_samples():
            if sample.ground_truth.detections is not None:
                for detection in sample.ground_truth.detections:
                    label = detection.label
                    if label not in label_counts:
                        label_counts[label] = 1
                    else:
                        label_counts[label] += 1

        # sort label counts by values and create list of only the keys of label counts in descending order
        sorted_label_counts = sorted(
            label_counts.items(), key=lambda x: x[1], reverse=True
        )
        labels = [label_count[0] for label_count in sorted_label_counts]
        values = [label_count[1] for label_count in sorted_label_counts]

        ctx.panel.state.labels = labels
        ctx.panel.state.values = values

        histogram_data = [
            {
                "x": ctx.panel.state.labels,
                "y": ctx.panel.state.values,
                "type": "bar",
                "marker": {"color": "orange"},
            }
        ]
        layout = {
            "width": 600,
            "xaxis": {"title": "Label Name"},
            "yaxis": {"title": "Count"},
            "title": "A Fancy Plot",
        }

        ctx.panel.state.histogram = histogram_data
        ctx.panel.state.layout = layout

    @staticmethod
    def on_change_ctx(ctx: ExecutionContext):
        # trigger actions when any change happens within fiftyone server
        pass

    @staticmethod
    def on_change_view(ctx: ExecutionContext):
        # trigger actions when any change happens within fiftyone view such as sample filtering
        pass

    def filter_data(self, ctx: ExecutionContext):
        filter_label = ctx.params["data"]["label"]
        # create a view of the dataset that only includes samples with the filter label
        filtered_view = ctx.dataset.filter_labels(
            "ground_truth", F("label") == filter_label
        )
        # display the filtered view
        ctx.trigger(
            "set_view",
            params=dict(
                view=json.loads(json_util.dumps(filtered_view._serialize()))
            ),
        )

    def reset(self, ctx: ExecutionContext):
        ctx.ops.clear_view()
        self.on_load(ctx)

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        # Bar Chart - Histogram
        panel.plot(
            "histogram",
            layout=ctx.panel.state.layout,
            label="Interactive Histogram",
            on_click=self.filter_data,
        )

        # Button
        panel.btn("reset", label="Reset Chart", on_click=self.reset)

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical"
            ),
        )


def register(p):
    p.register(CounterPanel)
    p.register(PlotPanel)
    p.register(MarkdownPanel)
    p.register(TablePanel)
    p.register(MediaPlayerPanel)
    p.register(ImagePanel)
    p.register(MultiViewPanel)
    p.register(DuplicatedPanel)
    p.register(InteractivePlot)
