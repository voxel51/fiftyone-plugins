import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.core.fields as fof
import itertools
import random

from textwrap import dedent

class IncCountPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="inc_count_panel",
            label="Example: Increment Count"
        )
    
    def on_load(self, ctx):
        print("Panel loaded")
        
    def render(self, ctx):
        panel = types.Object()
        grid = panel.grid('grid')
        grid.str('message', view=types.View(space=3))
        grid.btn('btn', label="+1", on_click=self.on_click)
        grid.btn('notify_btn', label="Notify", on_click=self.on_click_notify)
        choices = types.Choices()
        choices.add_choice(1, label="One")
        choices.add_choice(2, label="Two")
        choices.add_choice(3, label="Three")
        grid.enum('choice', values=choices.values(), on_change=self.on_change_choice)
        return types.Property(panel, view=types.GridView(height=100, align_x="center", align_y="center"))
    def on_click(self, ctx):
        grid = ctx.panel.state.grid or {}
        current_count = grid.get("count", 0)
        count = current_count + 1
        message = f"The count is {count}"
        ctx.panel.state.grid = {"message": message}
        ctx.panel.set_state('grid.count', count)
    def on_change_choice(self, ctx):
        print("Choice changed", ctx.panel.state)
        ctx.ops.notify(f"Choice changed to {ctx.panel.state.grid.get('choice', 'No choice')}")
    def on_click_notify(self, ctx):
        ctx.ops.notify(ctx.panel.state.grid.get("message", "No message"))

class CtxChangeEventsPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="ctx_change_events_panel",
            label="Example: Context Change Events"
        )
    
    def on_load(self, ctx):
        print("Panel loaded")
    
    def on_change_ctx(self, ctx):
        print("Context changed")
        current = ctx.panel.state.value or {}
        ctx.panel.state.value = {
            **current,
            "selected": ctx.selected,
            "view": ctx.view._serialize(),
            "current_sample": ctx.current_sample,
            "selected_labels": ctx.selected_labels,
        }

    # def on_change_selected(self, ctx):
    #     print("Selected changed")
    #     current = ctx.panel.state.value or {}
    #     ctx.panel.state.value = {
    #         **current,
    #         "selected": ctx.selected
    #     }

    # def on_change_view(self, ctx):
    #     print("View changed")
    #     current = ctx.panel.state.value or {}
    #     # this will cause an issue when used in conjunction with other ctx change events
    #     ctx.panel.state.value = {
    #         **current,
    #         "view": ctx.view._serialize()
    #     }

    # def on_change_current_sample(self, ctx):
    #     print("Current sample changed", ctx.current_sample)
    #     current = ctx.panel.state.value or {}
    #     recent_samples = current.get("recent_samples", [])
    #     recent_samples.append(ctx.current_sample)
    #     if ctx.current_sample:
    #         ctx.panel.state.value = {
    #             **current,
    #             "recent_samples": recent_samples
    #         }

    def render(self, ctx):
        panel = types.Object()
        panel.obj('value', view=types.JSONView())
        return types.Property(panel)

class TodoListPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="todo_list_panel",
            label="Example: Todo List"
        )
    
    def on_load(self, ctx):
        print("Panel loaded")
        ctx.panel.state.todos = [
            {"task": "Buy milk", "completed": False},
            {"task": "Walk the dog", "completed": True},
            {"task": "Do the dishes", "completed": False},
        ]

    def render(self, ctx):
        panel = types.Object()
        todo = types.Object()
        todo.bool('completed')
        todo.str('task')
        panel.list('todos', element_type=todo)
        panel.btn('clear_completed', label="Clear Completed", on_click=self.on_click_clear_complete)
        return types.Property(panel)

    def on_click_clear_complete(self, ctx):
        ctx.panel.state.todos = []
        # todos = ctx.panel.state.todos
        # ctx.panel.state.todos = [todo for todo in todos if not todo.get("completed", False)]


MAX_CATEGORIES = 100
COLOR_BY_TYPES = (
    fof.StringField,
    fof.BooleanField,
    fof.IntField,
    fof.FloatField,
)

PLOT_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "responsive": True,
    "displayModeBar": False
}

def create_plot_layout(state):
    style = state.style
    dragmode = state.drag_mode or "lasso"

    return {
        "dragmode": dragmode,
        "font": {
            "family": "var(--fo-fontFamily-body)",
            "size": 14
        },
        "showlegend": style == "categorical",
        "hovermode": False,
        "xaxis": {
            "showgrid": False,
            "zeroline": False,
            "visible": False
        },
        "yaxis": {
            "showgrid": False,
            "zeroline": False,
            "visible": False,
            "scaleanchor": "x",
            "scaleratio": 1
        },
        "autosize": True,
        "margin": {
            "t": 0,
            "l": 0,
            "b": 0,
            "r": 0,
            "pad": 0
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "legend": {
            "x": 1,
            "y": 1
        }
    }

class EmbeddingsPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="embeddings_panel",
            label="Example: Embeddings"
        )
    
    def on_load(self, ctx):
        self.load_plot_data(ctx)

    def on_selected(self, ctx):
        selected_points = ctx.params.get("data", [])
        selected_sample_ids = [sample.get("id", None) for sample in selected_points]
        if len(selected_sample_ids) > 0:
            ctx.ops.set_extended_selection(selected_sample_ids, scope="embeddings_panel")
            ctx.panel.state.selected = selected_sample_ids
        self.load_plot_data(ctx)


    def render(self, ctx):
        brain_key = ctx.panel.get_state("menu.actions.brain_key")
        panel = types.Object()
        
        brain_key_choices = types.Choices()
        valid_brain_keys = get_visualization_brain_keys(ctx.dataset)
        for brain_key in valid_brain_keys:
            brain_key_choices.add_choice(brain_key, label=brain_key)
        menu = panel.menu('menu', width=100, align_y="center")
        actions = menu.btn_group('actions')
        actions.enum('brain_key', placeholder="Brain key", values=brain_key_choices.values(), on_change=self.on_change_config, view=types.View(space=3))
        if brain_key:
            brain_info = ctx.dataset.get_brain_info(brain_key)
            color_by_fields = get_color_by_choices(ctx.dataset, brain_key, brain_info)
            label_choices = types.Choices()
            for field in color_by_fields:
                label_choices.add_choice(field, label=field)
            actions.enum('label_field', placeholder="Color by", values=label_choices.values(), on_change=self.on_change_config, view=types.View(space=3))
            if ctx.panel.state.selected:
                actions.btn('clear_selection', icon="clear", variant="outlined", label="Clear Selection", on_click=self.on_deselect)
            actions.btn('clear_zoom', icon="center_focus_weak", variant="outlined", label="Clear Zoom", on_click=self.on_click_clear_zoom)
            actions.btn('lasso_mode', icon="highlight_alt", variant="outlined", label="Select", on_click=self.on_click_lasso_mode)
            actions.btn('pan_mode', icon="open_with", variant="outlined", label="Pan", on_click=self.on_click_pan_mode)
            actions.btn('learn_more', icon="help", variant="outlined", label="Learn More", on_click=self.on_click_learn_more)
            plot_layout = create_plot_layout(ctx.panel.state)
            panel.plot('embeddings', config=PLOT_CONFIG, layout=plot_layout, on_selected=self.on_selected, on_deselect=self.on_deselect)
        return types.Property(panel)

    def on_click_learn_more(self, ctx):
        pass

    def on_click_clear_zoom(self, ctx):
        pass

    def on_click_lasso_mode(self, ctx):
        ctx.panel.state.drag_mode = "lasso"

    def on_click_pan_mode(self, ctx):
        ctx.panel.state.drag_mode = "pan"

    def on_change_extended_selection(self, ctx):
        extended_selection = (ctx.extended_selection or {}).get("selection", None)
        ctx.panel.state.selected = extended_selection
        print("Extended selection changed", extended_selection)
        self.load_plot_data(ctx)

    def on_change_view(self, ctx):
        self.load_plot_data(ctx)

    def on_deselect(self, ctx):
        ctx.panel.state.selected = None
        ctx.ops.set_extended_selection(reset=True, scope="embeddings_panel")

    def load_plot_data(self, ctx):
        dataset = ctx.dataset
        brain_key = ctx.panel.get_state("menu.actions.brain_key")
        label_field = ctx.panel.get_state("menu.actions.label_field")

        print("Loading plot data")
        # print('brain_key:', brain_key)
        # print('label_field:', label_field)
        if not brain_key:
            ctx.panel.state.embeddings = None
            return

        try:
            results = dataset.load_brain_results(brain_key)
            assert results is not None
        except:
            msg = (
                "Failed to load results for brain run with key '%s'. Try "
                "regenerating the results"
            ) % brain_key
            ctx.ops.notify(msg)
            ctx.panel.state.embeddings = None
            return

        view = ctx.view

        is_patches_view = view._is_patches

        patches_field = results.config.patches_field
        is_patches_plot = patches_field is not None

        # Determines which points from `results` are in `view`, which are the
        # only points we want to display in the embeddings plot
        if view.view() != results.view.view():
            results.use_view(view, allow_missing=True)

        # The total number of embeddings in `results`
        index_size = results.total_index_size

        # The number of embeddings in `results` that exist in `view`. Any
        # operations that we do with `results` can only work with this data
        available_count = results.index_size

        # The number of samples/patches in `view` that `results` doesn't have
        # embeddings for
        missing_count = results.missing_size

        points = results._curr_points
        if is_patches_plot:
            ids = results._curr_label_ids
            sample_ids = results._curr_sample_ids
        else:
            ids = results._curr_sample_ids
            sample_ids = itertools.repeat(None)

        # Color by data
        if label_field:
            if is_patches_view and not is_patches_plot:
                # Must use the root dataset in order to retrieve colors for the
                # plot, which is linked to samples, not patches
                view = view._root_dataset

            if is_patches_view and is_patches_plot:
                # `label_field` is always provided with respect to root
                # dataset, so we must translate for patches views
                _, root = dataset._get_label_field_path(patches_field)
                leaf = label_field[len(root) + 1 :]
                _, label_field = view._get_label_field_path(
                    patches_field, leaf
                )

            labels = view._get_values_by_id(
                label_field, ids, link_field=patches_field
            )

            field = view.get_field(label_field)

            if isinstance(field, fof.ListField):
                labels = [l[0] if l else None for l in labels]
                field = field.field

            if isinstance(field, fof.FloatField):
                style = "continuous"
            else:
                if len(set(labels)) <= MAX_CATEGORIES:
                    style = "categorical"
                else:
                    style = "continuous"
        else:
            labels = itertools.repeat(None)
            style = "uncolored"

        selected = itertools.repeat(True)

        traces_dict = create_embeddings_traces(style, points, ids, sample_ids, labels, selected)
        ctx.panel.state.style = style
        plot_selection = ctx.panel.state.selected
        ctx.panel.state.embeddings = traces_to_data(traces_dict, style, get_color, plot_selection, None, [], None)
    
    def on_change_config(self, ctx):
        self.load_plot_data(ctx)

def traces_to_data(traces, style, get_color, plot_selection, selection_style, colorscale, setting):
    is_categorical = style == "categorical"
    is_continuous = style == "continuous"
    is_uncolored = style == "uncolored"

    # Helper function to convert color values
    def convert_color(c):
        return f"rgb({c[0]}, {c[1]}, {c[2]})"

    # Sort traces and apply transformations
    sorted_traces = sorted(traces.items(), key=lambda x: x[0])
    result = []

    for key, trace in sorted_traces:
        selected_points = [get_point_index(trace, id_) for id_ in plot_selection] if plot_selection else None
        # print('plot_selection------------')
        # print(plot_selection)
        # print('selected_points------------')
        # print(selected_points)
        # TODO impl selected points
        # selected_points = [] #[p for p in selected_points if p is not None]

        color = (255, 165, 0) # get_label_color(key, setting) or convert_color(get_color(key)) or (255, 165, 0)  # Default orange
        
        mapped_colorscale = [(idx / (len(colorscale) - 1), convert_color(Color.from_css_rgb_values(*c))) for idx, c in enumerate(colorscale)]

        result.append({
            "x": trace["x"],
            "y": trace["y"],
            "ids": trace["ids"],
            "type": "scattergl",
            "mode": "markers",
            "marker": {
                "autocolorscale": not is_continuous,  # True for isCategorical or isUncolored
                "colorscale": mapped_colorscale,
                "color": convert_color(color) if is_categorical else (None if is_uncolored else trace['labels']),
                "size": 6,
                "colorbar": None if (is_categorical or is_uncolored) else {
                    "lenmode": "fraction",
                    "x": 1,
                    "y": 0.5,
                },
            },
            "name": key,
            "selectedpoints": selected_points,
            "selected": {
                "marker": {
                    "opacity": 1,
                    "size": 10 if selection_style == "selected" else 6,
                    "color": "orange" if selection_style == "selected" else None,
                },
            },
            "unselected": {
                "marker": {
                    "opacity": 0.2,
                },
            },
        })

    return result

def get_point_index(trace, id_):
    try:
        return trace["ids"].index(id_)
    except ValueError:
        return None

def get_label_color(key, setting):
    # Implementation needed
    pass

def get_color(key):
    # Implementation needed
    pass

# Assuming the implementation for `Color.from_css_rgb_values` is defined elsewhere
class Color:
    @staticmethod
    def from_css_rgb_values(r, g, b):
        return (r, g, b)


def get_visualization_brain_keys(dataset):
    visualization_keys = []
    for brain_key in dataset.list_brain_runs():
        brain_info = dataset.get_brain_info(brain_key)
        if 'visualization' in brain_info.config.cls.lower():
            visualization_keys.append(brain_key)

    return visualization_keys

def create_embeddings_traces(style, points, ids, sample_ids, labels, selected):
    traces = {}
    for data in zip(points, ids, sample_ids, labels, selected):
        add_to_trace(traces, style, *data)
    return traces

def add_to_trace(traces, style, points, id, sample_id, label, selected):
    key = label if style == "categorical" else "points"
    if key not in traces:
        traces[key] = {"x": [], "y": [], "ids": [], "labels": [], "selected": selected}

    # add to plotly style trace where x, y, etc are arrays
    traces[key]["x"].append(points[0])
    traces[key]["y"].append(points[1])
    traces[key]["ids"].append(id)
    traces[key]["labels"].append(label)


    # traces[key].append(
    #     {
    #         "points": points,
    #         "id": id,
    #         "sample_id": sample_id or id,
    #         "label": label,
    #         "selected": selected,
    #     }
    # )

def get_sample_filter(slices):
    # Placeholder for actual sample filter logic
    pass

def get_selected_ids(data, brain_key):
    dataset = ctx.dataset
    results = dataset.load_brain_results(brain_key)
    view = ctx.view

    if view.view() != results.view.view():
        results.use_view(view, allow_missing=True)

    patches_field = results.config.patches_field
    is_patches_plot = patches_field is not None
    ids = results._curr_label_ids if is_patches_plot else results._curr_sample_ids

    selected_ids = handle_extended_selection(data, ctx.view, ids, is_patches_plot)
    return list(selected_ids) if selected_ids else None

def handle_extended_selection(data, view, ids, is_patches_plot, extended_selection=None):
    extended_view = view

    is_patches_view = extended_view._is_patches
    extended_ids = collect_ids(extended_view, is_patches_view, is_patches_plot, data.get("patchesField"))

    selected_ids = set(ids) & set(extended_ids) if extended_ids else None

    if extended_selection is not None:
        if selected_ids:
            selected_ids &= extended_selection
        else:
            selected_ids = extended_selection

    return selected_ids

def collect_ids(view, is_patches_view, is_patches_plot, patches_field):
    if is_patches_plot and not is_patches_view:
        _, id_path = view._get_label_field_path(patches_field, "id")
        return view.values(id_path, unwind=True)
    elif is_patches_view and not is_patches_plot:
        return view.values("sample_id")
    return view.values("id")

def get_color_by_choices(dataset, brain_key, brain_info):
    info = dataset.get_brain_info(brain_key)
    patches_field = info.config.patches_field
    is_patches_plot = patches_field is not None

    schema = dataset.get_field_schema(flat=True)

    if is_patches_plot:
        _, root = dataset._get_label_field_path(patches_field)
        root += "."
        schema = {k: v for k, v in schema.items() if k.startswith(root)}

    bad_roots = tuple(
        k + "." for k, v in schema.items() if isinstance(v, fof.ListField)
    )

    fields = [
        path
        for path, field in schema.items()
        if (
            (
                isinstance(field, COLOR_BY_TYPES)
                or (
                    isinstance(field, fof.ListField)
                    and isinstance(field.field, COLOR_BY_TYPES)
                )
            )
            and not path.startswith(bad_roots)
        )
    ]

    return fields


def get_markdown(value, clicked):
    if clicked:
        return dedent(f"""
        ### Computing visualization

        Please wait while we compute the visualization.
        """)

    if value >= 3:
        return dedent(f"""
        ### Good job!

        You've selected {value} samples.
        
        #### Did you know you can do this in python?

        ```python
        import fiftyone as fo
        import fiftyone.zoo as foz

        # Load a sample dataset
        dataset = foz.load_zoo_dataset("quickstart")

        # Launch the FiftyOne app
        session = fo.launch_app(dataset)

        # Get a list of sample IDs to select (for example, the first 5 samples)
        sample_ids = [sample.id for sample in dataset[:{value}]]

        # Select the samples in the app
        session.selected = sample_ids
        session.refresh()
        ```
    
        #### Let's keep going...

        Click the button below to start the process!
        """)

    return dedent(f"""
    ### Let's compute visualization!

    First lets select a few samples.
    """)

def get_random_markdown(idx):
    examples = [
        dedent("""
        ### Example 1
        
        This is an example of a markdown item.
        """),
        dedent("""
        ### Example 2
               
        - list item 1
        - list item 2
        - list item 3
        """),
        dedent("""
        ### Example 3
               
        ```python
        # code block
        print("Hello, world!")
        ```
        """)     
    ]

    return examples[idx]



class DashboardExamplePanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="dashboard_example_panel",
            label="Example: Dashboard"
        )
    
    def on_load(self, ctx):
        ctx.panel.state.dashboard = ctx.panel.state.dashboard or {}
        ctx.panel.state.editable = True

    def on_click_add_chart(self, ctx):
        dashboard = ctx.panel.state.dashboard
        count = len(dashboard)
        new_key = f"plot{count + 1}"
        dashboard[new_key] = {
            "x": [1, 2, 3, 4, 5],
            "y": [random.randint(1, 20) for _ in range(5)]
        }
        ctx.panel.state.dashboard = dashboard

    def on_click_clear(self, ctx):
        ctx.panel.set_state('dashboard', None)
        ctx.panel.state.dashboard = {}
        ctx.panel.state.md_items = None
        ctx.panel.state.md_items = {}
        ctx.panel.state.layout = None

    def on_close_item(self, ctx):
        id = ctx.params.get('id')
        dashboard = ctx.panel.state.dashboard
        del dashboard[id]
        ctx.panel.state.dashboard = {}
        ctx.panel.state.dashboard = dashboard
        # md_items = ctx.panel.state.md_items 
        # del md_items[id]
        # ctx.panel.state.md_items = {}
        # ctx.panel.state.md_items = md_items

    def on_click_add_md(self, ctx):
        md_items = ctx.panel.state.md_items or {}
        count = len(md_items)
        new_key = f"md{count + 1}"
        md_items[new_key] = get_random_markdown(count % 3)
        ctx.panel.state.md_items = md_items

    def on_layout_change(self, ctx):
        print("Layout changed", ctx.params)
        ctx.panel.state.layout = ctx.params.get("layout", None)

    def on_click_toggle_editable(self, ctx):
        ctx.panel.state.editable = not ctx.panel.state.editable

    def render(self, ctx):
        editable = ctx.panel.state.editable
        layout = ctx.params.get("layout", None)
        panel = types.Object()
        panel.btn('toggle_editable', label="Toggle Editable", on_click=self.on_click_toggle_editable)
        dashboard = panel.dashboard('dashboard', height=100, allow_addition=editable, allow_deletion=editable, layout=layout, on_add_item=self.on_click_add_chart, on_close_item=self.on_close_item, on_layout_change=self.on_layout_change)
        for key, value in ctx.panel.state.dashboard.items():
            dashboard.plot(key)
        return types.Property(panel)


class EvaluationLitePanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="evaluation_lite_panel",
            label="Evaluation Lite"
        )
    
    def on_load(self, ctx):
        ctx.panel.state.evaluations = [
            {"name": "Accuracy", "value": 0.85, "description": "The accuracy of the model"},
            {"name": "Precision", "value": 0.75, "description": "The precision of the model"},
            {"name": "Recall", "value": 0.65, "description": "The recall of the model"},
        ]
        ctx.panel.state.plot1 = {
            "type": "scatter",
            "x": [1, 2, 3, 4, 5],
            "y": [random.randint(1, 20) for _ in range(5)]
        }
        ctx.panel.state.plot2 = {
            "type": "heatmap",
            "x": [1, 2, 3, 4, 5],
            "y": [random.randint(1, 20) for _ in range(5)],
            "z": [random.randint(1, 20) for _ in range(5)]
        }

        pass

    def render(self, ctx):
        panel = types.Object()
        item_obj = types.Object()
        item_obj.str('name')
        item_obj.float('value')
        item_obj.str('description')

        table_view = types.TableView() 
        table_view.add_column('name')
        table_view.add_column('value')
        table_view.add_column('description')
        panel.list('evaluations', element_type=item_obj, view=table_view)

        panel.plot('plot1', space=6)
        panel.plot('plot2', space=6)
        return types.Property(panel)

def register(p):
    p.register(IncCountPanel)
    p.register(TodoListPanel)
    p.register(CtxChangeEventsPanel)
    p.register(EmbeddingsPanel)
    p.register(DashboardExamplePanel)
    p.register(EvaluationLitePanel)
