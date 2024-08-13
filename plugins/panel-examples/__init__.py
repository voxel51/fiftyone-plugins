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
        return foo.PanelConfig(
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
            on_click=self.say_hi,
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


###
# Plot
###


class PlotPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
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

        ctx.panel.data.data = plot_data

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        # grab data field from state and render it in a plotly view
        panel.plot("data", label="Plotly Panel")  # shortcut for plot creation

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
        return foo.PanelConfig(
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
        return foo.PanelConfig(
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
        return foo.PanelConfig(
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
        return foo.PanelConfig(
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
        return foo.PanelConfig(
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
        return foo.PanelConfig(
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
        ctx.panel.data.plot = [
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
        return foo.PanelConfig(
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

def get_view_for_category(field, category, view):
    is_label_field = field.endswith(".label")
    is_tag_field = field.endswith("tags")
    if is_label_field:
        parent_field = field.split(".")[0]
        return view.filter_labels(parent_field, F('label') == category)
    elif is_tag_field:
        return view.match_tags(category)
    else:
        return view.match(F(field) == category)
    return None

class InteractivePlot(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_interactive_plot",
            label="Python Panel Example: Interactive Plot",
        )

    def on_load(self, ctx: ExecutionContext):
        target_field = ctx.panel.state.target_field or "ground_truth.detections.label"
        ctx.panel.state.target_field = target_field
        counts = ctx.dataset.count_values(target_field)
        raw_keys = list(counts.keys())
        keys = [str(k) for k in raw_keys]
        sorted_items = sorted(zip(keys, counts.values()), key=lambda x: x[0])
        keys, values = zip(*sorted_items)

        histogram_data = {
            'x': keys,
            'y': values,
            'type': 'bar'
        }

        ctx.panel.data.histogram = histogram_data

    def on_change_view(self, ctx: ExecutionContext):
        self.on_load(ctx)

    def filter_data(self, ctx: ExecutionContext):
        x = ctx.params.get("x")
        view = get_view_for_category(ctx.panel.state.target_field, x, ctx.dataset)
        if view:
            ctx.ops.set_view(view)

    def reset(self, ctx: ExecutionContext):
        ctx.ops.clear_view()
        self.on_load(ctx)

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        # Bar Chart - Histogram
        panel.plot(
            "histogram",
            layout={
                "title": {
                    'text': "Interactive Histogram",
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'automargin': True
                },
                "xaxis": {"title": "Labels"},
                "yaxis": {"title": "Count"},
            },
            on_click=self.filter_data,
            width=100
        )

        # Button
        panel.btn("reset", label="Reset Chart", on_click=self.reset, variant="contained")

        return types.Property(
            panel,
            view=types.GridView(
                align_x="center", align_y="center", orientation="vertical",
                height=100, width=100, gap=2, padding=0
            ),
        )


###
# Dropdown Menu
###


class DropdownMenuPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_dropdown_menu",
            label="Python Panel Example: Dropdown Menu",
        )

    def on_load(self, ctx: ExecutionContext):
        ctx.panel.state.selection = None

    def alter_selection(self, ctx: ExecutionContext):
        ctx.panel.state.selection = ctx.params["value"]

    def refresh_page(self, ctx: ExecutionContext):
        ctx.ops.reload_dataset()

    def reload_samples(self, ctx: ExecutionContext):
        ctx.ops.reload_samples()

    def say_hi(self, ctx: ExecutionContext):
        ctx.ops.notify("Hi!", variant="success")

    def render(self, ctx: ExecutionContext):
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

        # define a dropdown menu and add choices
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

        # add dropdown menu to the panel as a view, and use the on_change callback method to trigger the alter_selection function
        menu.str(
            "dropdown",
            view=dropdown,
            label="Dropdown Menu",
            on_change=self.alter_selection,
        )

        # change panel visual state dependent on dropdown menu selection
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


###
# Walkthrough Tutorial
###


class WalkthroughTutorialPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="example_walkthrough_tutorial",
            label="Python Panel Example: Walkthrough Tutorial",
        )

    def on_load(self, ctx: ExecutionContext):
        ctx.panel.state.page = 1

        info_table = [
            {
                "Dataset Name": f"{ctx.dataset.name}",
                "Dataset Description": "FiftyOne Quick Start Zoo Dataset",
                "Number of Samples": f"{ctx.dataset.count()}",
            },
        ]

        ctx.panel.state.info_table = info_table

    def go_to_next_page(self, ctx: ExecutionContext):
        ctx.panel.state.page = ctx.panel.state.page + 1

    def go_to_previous_page(self, ctx: ExecutionContext):
        ctx.panel.state.page = ctx.panel.state.page - 1

    def reset_page(self, ctx: ExecutionContext):
        ctx.panel.state.page = 1

    def open_operator_io(self, ctx: ExecutionContext):
        ctx.ops.open_panel("OperatorIO")

    def render(self, ctx: ExecutionContext):
        panel = types.Object()

        # define a vertical stack to live inside your panel
        stack = panel.v_stack(
            "welcome", gap=2, width=75, align_x="center", align_y="center"
        )
        button_container = types.GridView(
            gap=2, align_x="left", align_y="center"
        )

        page = ctx.panel.get_state("page", 1)
        panel.arrow_nav(
            "page_nav",
            on_forward=self.go_to_next_page,
            on_backward=self.go_to_previous_page,
            forward=page < 3,
            backward=page > 1,
        )

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

        return types.Property(
            panel,
            view=types.GridView(
                height=100, width=100, align_x="center", align_y="center"
            ),
        )


# Utility function to enhance styling of navigation buttons
def add_panel_navigation(
    panel, left=True, right=False, on_left=None, on_right=None
):
    base_btn_styles = {
        "position": "absolute",
        "top": "50%",
        "minWidth": 0,
        "padding": "8px",
        "background": "#333333",
        "&:hover": {"background": "#2b2a2a"},
    }
    if left:
        panel.btn(
            "previous",
            label="Previous",
            icon="arrow_back",
            variant="contained",
            componentsProps={"button": {"sx": {**base_btn_styles, "left": 8}}},
            on_click=on_left,
        )
    if right:
        panel.btn(
            "next",
            label="Next",
            icon="arrow_forward",
            variant="contained",
            componentsProps={
                "button": {"sx": {**base_btn_styles, "right": 8}}
            },
            on_click=on_right,
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
    p.register(DropdownMenuPanel)
    p.register(WalkthroughTutorialPanel)
