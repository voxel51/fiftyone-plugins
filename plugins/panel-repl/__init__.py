"""
Panel REPL

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import enum
import numpy as np
import random
import json
from textwrap import dedent

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

examples = {
    "REPL": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.md("# REPL Panel")
                panel.btn("click_me", label="Click Me", on_click=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Hello World": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.md("# Hello, world!")
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Simple Button": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.btn("click_me", label="Click Me", on_click=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Dropdown Menu": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                choices = types.Choices()
                choices.add_choice("option_1", label="Option 1")
                choices.add_choice("option_2", label="Option 2")
                panel.enum("dropdown", values=choices.values(), view=choices, on_change=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "dropdown": "option_2"
        }
    },
    "Simple Table": {
        "render_src": dedent("""
            def render(ctx):
                table = types.TableView()
                table.add_column("name", label="Name")
                table.add_column("value", label="Value")
                panel = types.Object()
                panel.list("simple_table", types.Object(), view=table)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "simple_table": [
                {"name": "Alice", "value": 25},
                {"name": "Bob", "value": 30},
                {"name": "Charlie", "value": 35}
            ]
        }
    },
    "Histogram": {
        "render_src": dedent("""
            def render(ctx):
                layout = {
                    "title": "Random Values Histogram",
                    "xaxis": {"title": "Values"},
                    "yaxis": {"title": "Frequency"}
                }
                panel = types.Object()
                panel.plot("histogram_plot", layout=layout, on_click=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "histogram_plot": {
                "type": "histogram",
                "x": np.random.randn(100).tolist(),
                "nbinsx": 30,
                "marker": {"color": "blue"}
            }
        }
    },
    "Scatter Plot": {
        "render_src": dedent("""
            def render(ctx):
                layout = {
                    "title": "Random Scatter Plot",
                    "xaxis": {"title": "X-axis"},
                    "yaxis": {"title": "Y-axis"}
                }
                panel = types.Object()
                panel.plot("scatter_plot", layout=layout, on_select=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "scatter_plot": {
                "type": "scatter",
                "mode": "markers",
                "x": np.random.rand(100).tolist(),
                "y": np.random.rand(100).tolist(),
                "marker": {"size": 10, "color": "green"}
            }
        }
    },
    "Line Plot": {
        "render_src": dedent("""
            def render(ctx):
                layout = {
                    "title": "Sine Wave",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "Amplitude"}
                }
                panel = types.Object()
                panel.plot("line_plot", type="scatter", layout=layout)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "line_plot": {
                "mode": "lines",
                "x": np.linspace(0, 10, 100).tolist(),
                "y": np.sin(np.linspace(0, 10, 100)).tolist()
            }
        }
    },
    "Pie Chart": {
        "render_src": dedent("""
            def render(ctx):
                layout = {"title": "Market Share"}
                panel = types.Object()
                panel.plot("pie_chart", layout=layout, on_click=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "pie_chart": {
                "type": "pie",
                "labels": ["Company A", "Company B", "Company C", "Company D"],
                "values": [30, 20, 25, 25],
                "marker": {"colors": ["red", "blue", "green", "purple"]}
            }
        }
    },
    "Markdown": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.md("## Markdown Example\\nThis is an example of using **Markdown** in a panel.\\n\\n- Bullet 1\\n- Bullet 2\\n- Bullet 3")
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Tuples": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.tuple(
                    "key_value_pairs",
                    types.String(),
                    types.Number(int=True),
                    label="Key-Value Pairs",
                    on_change=test_event
                )
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "key_value_pairs": ["My String", 42]
        }
    },
    "Image": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                img_view = types.ImageView()
                panel.str("sample_image", label="Sample Image", view=img_view)
                return types.Property(panel)

        """).lstrip(),
        "json_state": {
            "sample_image": "https://via.placeholder.com/300"
        }
    },
    "Slider": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                slider = types.SliderView()
                panel.int("slider_value", view=slider, label="Slider", on_change=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "slider_value": 75
        }
    },
    "Checkbox": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.bool("checkbox_value", label="Enable Feature", on_change=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "checkbox_value": True
        }
    },
    "Progress Bar": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                progress_view = types.ProgressView(label="Loading...", variant="linear")
                panel.float("progress", view=progress_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "progress": 0.5
        }
    },
    "Radio Buttons": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                radio_choices = types.RadioGroup(label="Choose an option")
                radio_choices.add_choice("option_1", label="Option 1")
                radio_choices.add_choice("option_2", label="Option 2")
                panel.enum("radio_selection", values=radio_choices.values(), view=radio_choices, on_change=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "radio_selection": "option_1"
        }
    },
    "Tabbed View": {
        "render_src": dedent("""
            def render(ctx):
                tabs_view = types.TabsView(label="Tabbed View")
                tab_1 = types.Object()
                tab_1.md("## Tab 1 Content")
                tab_2 = types.Object()
                tab_2.md("## Tab 2 Content")
                panel = types.Object()
                panel.list("tabs", types.Object(), view=tabs_view)
                panel.add_property("tab_1", tab_1)
                panel.add_property("tab_2", tab_2)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "tabs": [{"name": "Tab 1", "value": "tab_1"}, {"name": "Tab 2", "value": "tab_2"}]
        }
    },
    "Heatmap": {
        "render_src": dedent("""
            def render(ctx):
                layout = {
                    "title": "Heatmap Example",
                    "xaxis": {"title": "X-axis"},
                    "yaxis": {"title": "Y-axis"}
                }
                panel = types.Object()
                panel.plot("heatmap", layout=layout)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "heatmap": {
                "type": "heatmap",
                "z": [
                    [1, 20, 30],
                    [20, 1, 60],
                    [30, 60, 1]
                ],
                "x": ["A", "B", "C"],
                "y": ["X", "Y", "Z"]
            }
        }
    },
    "Bar Chart": {
        "render_src": dedent("""
            def render(ctx):
                layout = {
                    "title": "Bar Chart Example",
                    "xaxis": {"title": "Categories"},
                    "yaxis": {"title": "Values"}
                }
                panel = types.Object()
                panel.plot("bar_chart", layout=layout)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "bar_chart": {
                "type": "bar",
                "x": ["Category A", "Category B", "Category C"],
                "y": [20, 35, 50],
                "marker": {"color": ["red", "blue", "green"]}
            }
        }
    },
    "Toggle Switch": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                switch_view = types.SwitchView(label="Toggle Switch")
                panel.bool("toggle", view=switch_view, on_change=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "toggle": False
        }
    },
    "File Upload": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                file_view = types.FileView(types="image/*", max_size=1048576)
                panel.str("uploaded_file", label="Upload Image", view=file_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "uploaded_file": None
        }
    },
    "Key-Value Editor": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                key_value_view = types.KeyValueView()
                panel.map("key_value_editor", view=key_value_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "key_value_editor": {
                "Key 1": "Value 1",
                "Key 2": "Value 2"
            }
        }
    },
    "JSON Viewer": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                json_view = types.JSONView()
                panel.str("json_data", label="JSON Data", view=json_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "json_data": '{"name": "John", "age": 30, "city": "New York"}'
        }
    },
    "Autocomplete Input": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                autocomplete_view = types.AutocompleteView()
                autocomplete_view.add_choice("Apple", label="Apple")
                autocomplete_view.add_choice("Banana", label="Banana")
                autocomplete_view.add_choice("Cherry", label="Cherry")
                panel.str("autocomplete_input", label="Select Fruit", view=autocomplete_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "autocomplete_input": "Banana"
        }
    },
    "Collapsible Sections": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.collapse(
                    "section_1",
                    types.Object(),
                    label="Section 1",
                    description="This is the first section"
                )
                panel.collapse(
                    "section_2",
                    types.Object(),
                    label="Section 2",
                    description="This is the second section"
                )
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "section_1": {"collapsed": False},
            "section_2": {"collapsed": True}
        }
    },
    "Markdown with Links": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.md("## Markdown with Links\\nThis is an [example link](https://example.com).")
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Notification Banner": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                panel.notice("This is a notification banner.", severity="info")
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Simple Grid": {
        "render_src": dedent("""
            def render(ctx):
                grid_view = types.GridView(gap=2)
                panel = types.Object()
                panel.list("grid_items", types.Object(), view=grid_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "grid_items": [{"item": "Item 1"}, {"item": "Item 2"}, {"item": "Item 3"}]
        }
    },
    "Embedded Media Player": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                media_view = types.MediaPlayerView()
                panel.str("media_url", label="Play Video", view=media_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "media_url": "https://www.w3schools.com/html/mov_bbb.mp4"
        }
    },
    "Slider Range": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                range_slider = types.SliderView()
                panel.array("range_values", element_type=types.Int(), view=range_slider, label="Select Range", on_change=test_event)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "range_values": [20, 80]
        }
    },
    "Icon Button": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                icon_button = types.IconButtonView(icon="favorite", label="Like", on_click=test_event)
                panel.view("icon_btn", icon_button)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {}
    },
    "Tree View": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                tree_view = types.Object()
                tree_view.str("label", label="Label")
                panel.tree("tree_structure", types.Object(), view=tree_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "tree_structure": {
                "label": "Root",
                "children": [
                    {"label": "Child 1"},
                    {"label": "Child 2", "children": [{"label": "Grandchild 1"}, {"label": "Grandchild 2"}]}
                ]
            }
        }
    },
    "Toggle Button Group": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                toggle_view = types.ButtonGroupView()
                panel.str("toggle_group", label="Toggle Options", view=toggle_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "toggle_group": "option_1"
        }
    },
    "Stepper": {
        "render_src": dedent("""
            def render(ctx):
                panel = types.Object()
                stepper_view = types.StepperView()
                panel.int("current_step", label="Current Step", view=stepper_view)
                return types.Property(panel)
        """).lstrip(),
        "json_state": {
            "current_step": 2,
            "steps": [
                {"label": "Step 1", "description": "This is step 1"},
                {"label": "Step 2", "description": "This is step 2"},
                {"label": "Step 3", "description": "This is step 3"}
            ]
        }
    }
}



test_event = "@voxel51/panel_repl/panel_repl#on_test_event"

def get_property_from_src(render_src, ctx):
    # Define a local scope for execution
    local_scope = {"test_event": test_event}
    
    # Execute the code in a safe context
    try:
        exec(render_src, globals(), local_scope)
        render_func = local_scope.get("render")
        if render_func:
            # Call the render function and update the panel
            property = render_func(ctx)
            return property
        else:
            raise ValueError("No render function defined in the provided code.")
    except Exception as e:
        print(f"Error: {str(e)}")

class PanelRepl(foo.Panel):
    preview_property = None
    
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="panel_repl",
            label="Panel REPL"
        )
    
    def on_test_event(self, ctx):
        ctx.params.pop('panel_state')
        ctx.panel.set_state('split.left.test_event_params', {
            "params": ctx.params
        })
    
    def on_example_change(self, ctx):
        example_key = ctx.panel.state.example
        example = examples.get(example_key)
        if example:
            ctx.panel.set_state('split.left.repl_render_src', example["render_src"])
            ctx.panel.set_state('split.left.render_src', example["render_src"])
            ctx.panel.set_state('json_state', json.dumps(example["json_state"], indent=2))
            example_state = example["json_state"]
            ctx.panel.set_state('split.right.preview_property', example_state)
    
    def on_src_changed(self, ctx):
        pass

    def on_state_src_changed(self, ctx):
        try:
            parsed_state = json.loads(ctx.panel.get_state('json_state'))
        except:
            parsed_state = {}
        ctx.panel.set_state('split.right.preview_property', parsed_state)

    def on_reset(self, ctx):
        print("Resetting panel")
        ctx.panel.set_state('example', None)

    def render(self, ctx):
        selected_example = ctx.panel.state.example
        print('example_key', selected_example)
        panel = types.Object()
        code_view = types.CodeView(language="python", width=33)
        json_view = types.CodeView(language="json", width=33)
        
        # Add dropdown menu for examples
        example_choices = types.Choices()
        for example_key in examples.keys():
            example_choices.add_choice(example_key, label=example_key)

        panel.btn('reset', label="Reset", on_click=self.on_reset)
        panel.enum("example", values=example_choices.values(), view=example_choices, label="Choose an Example", on_change=self.on_example_change)
        render_src = None
        if selected_example == "REPL":
            render_src = ctx.panel.get_state('split.left.repl_render_src')
        else:
            render_src = ctx.panel.get_state('split.left.render_src')
        split = panel.h_stack('split')
        left = split.v_stack('left', width=45)
        right = split.v_stack('right', width=45)
        if selected_example:
            read_only_code_view = types.CodeView(language="python", width=33, read_only=True)
            left.str('example_src', label="Example Source", read_only=True, default=examples[selected_example]["render_src"], view=read_only_code_view)
            if selected_example == "REPL":
                left.str('repl_render_src', label="REPL", default=render_src, view=code_view, on_change=self.on_src_changed)
            elif selected_example:
                left.str('render_src', label="render()", default=render_src, view=code_view, on_change=self.on_src_changed)
            panel.str('json_state', label="State Editor", view=json_view, on_change=self.on_state_src_changed)
            left.obj('current_state', label="Current State", default=ctx.panel.get_state('right.preview_property'), view=types.JSONView(width=33))
            left.obj('test_event_params', label="Test Event Params", view=types.JSONView(width=33))
        
        if render_src:
            preview_property = get_property_from_src(render_src, ctx)
            if isinstance(preview_property, types.Property):
                right.md("### Preview")
                right.add_property('preview_property', preview_property)
        
        return types.Property(panel)

def register(p):
    p.register(PanelRepl)
