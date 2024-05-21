import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.core.fields as fof
import itertools

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
        return types.Property(panel)
    def on_click(self, ctx):
        grid = ctx.panel.state.grid or {}
        current_count = grid.get("count", 0)
        count = current_count + 1
        message = f"The count is {count}"
        ctx.panel.state.grid = {"count": count, "message": message}
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
        # print(ctx.params)
        selected_points = ctx.params.get("data", [])
        selected_sample_ids = [sample.get("id", None) for sample in selected_points]
        print(selected_sample_ids)
        if len(selected_sample_ids) > 0:
            ctx.ops.show_samples(selected_sample_ids, use_extended_selection=True)


    def render(self, ctx):
        brain_key = ctx.panel.state.brain_key
        panel = types.Object()
        brain_key_choices = types.Choices()
        valid_brain_keys = get_visualization_brain_keys(ctx.dataset)
        for brain_key in valid_brain_keys:
            brain_key_choices.add_choice(brain_key, label=brain_key)
        panel.enum('brain_key', values=brain_key_choices.values(), on_change=self.on_change_config, view=types.View(space=3))
        if brain_key:
            brain_info = ctx.dataset.get_brain_info(brain_key)
            color_by_fields = get_color_by_choices(ctx.dataset, brain_key, brain_info)
            label_choices = types.Choices()
            for field in color_by_fields:
                label_choices.add_choice(field, label=field)
            panel.enum('label_field', values=label_choices.values(), on_change=self.on_change_config, view=types.View(space=3))
            plot_layout = create_plot_layout(ctx.panel.state)
            panel.plot('embeddings', config=PLOT_CONFIG, layout=plot_layout, on_selected=self.on_selected)
        return types.Property(panel)

    def load_plot_data(self, ctx):
        dataset = ctx.dataset
        brain_key = ctx.panel.state.brain_key
        label_field = ctx.panel.state.label_field

        print("Loading plot data")
        print('brain_key:', brain_key)
        print('label_field:', label_field)
        if not brain_key or not label_field:
            return

        try:
            results = dataset.load_brain_results(brain_key)
            assert results is not None
        except:
            msg = (
                "Failed to load results for brain run with key '%s'. Try "
                "regenerating the results"
            ) % brain_key
            return {"error": msg}

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
        ctx.panel.state.embeddings = traces_to_data(traces_dict, style, get_color, None, None, [], None)
        


    
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
        # TODO impl selected points
        selected_points = [] #[p for p in selected_points if p is not None]

        color = (255, 165, 0) # get_label_color(key, setting) or convert_color(get_color(key)) or (255, 165, 0)  # Default orange
        
        mapped_colorscale = [(idx / (len(colorscale) - 1), convert_color(Color.from_css_rgb_values(*c))) for idx, c in enumerate(colorscale)]

        print(trace)

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
    # Implementation needed
    pass

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


def get_markdown(value):
    if value is 3:
        return dedent(f"""
        ### Good job!

        You've selected {value} samples.
        """)

    return dedent(f"""
    ### Try FiftyOne

    This is a tutorial panel. You can use this panel to display markdown content and interact with the dataset.

    You can use the buttons below to interact with the panel.

    ##### Notify

    Click the "Notify" button to display a notification with the message you provide.

    ##### Example

    ```python
    ctx.ops.notify("Hello, world!")
    ```

    ##### Dynamic Content

    This value here: {value} is dynamic.

    """)

class TutorialPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="tutorial_panel",
            label="Tutorial Panel"
        )
    
    def on_load(self, ctx):
        print("Panel loaded")
    
    def render(self, ctx):
        count = ctx.panel.state.count or 0
        panel = types.Object()
        panel.str('message', view=types.MarkdownView(), default=get_markdown(count))
        panel.btn('btn', label="Notify", on_click=self.on_click)
        panel.btn('btn2', label="Compute Similarity", prompt=True, on_click="@voxel51/brain/compute_similarity")
        return types.Property(panel)
    
    def on_click(self, ctx):
        ctx.ops.notify("Hello World")

    def on_change_selected(self, ctx):
        ctx.panel.state.count = len(ctx.selected)
        print("Selected changed", ctx.selected)

def register(p):
    p.register(IncCountPanel)
    p.register(TodoListPanel)
    p.register(CtxChangeEventsPanel)
    p.register(EmbeddingsPanel)
    p.register(TutorialPanel)
