"""
Dashboard plugin.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

from datetime import datetime, timedelta
from enum import Enum
import random
from textwrap import dedent

import numpy as np

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone import ViewField as F


class PlotlyPlotType(Enum):
    BAR = "bar"
    SCATTER = "scatter"
    LINE = "line"
    PIE = "pie"


class PlotType(Enum):
    CATEGORICAL_HISTOGRAM = "categorical_histogram"
    NUMERIC_HISTOGRAM = "numeric_histogram"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"


NUMERIC_TYPES = (fo.IntField, fo.FloatField, fo.DateTimeField, fo.DateField)
CATEGORICAL_TYPES = (fo.StringField, fo.BooleanField)
REQUIRES_X = [PlotType.SCATTER, PlotType.LINE, PlotType.NUMERIC_HISTOGRAM]
REQUIRES_Y = [PlotType.SCATTER, PlotType.LINE]
CONFIGURE_PLOT_URI = "@voxel51/dashboard/configure_plot"


class DashboardPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="dashboard",
            label="Dashboard",
            icon="dashboard",
            allow_multiple=True,
        )

    def on_load(self, ctx):
        # There are several places where we are clearing state.items
        # this is a workaround to a core issue that once fixed this can be removed
        # See https://github.com/voxel51/fiftyone-plugins/pull/153 for more details
        ctx.panel.state.items = None
        dashboard_state = DashboardState(ctx)
        dashboard_state.load_all_plot_data()

    def on_change_view(self, ctx):
        dashboard_state = DashboardState(ctx)
        for item in dashboard_state.items:
            if item.update_on_change:
                data = dashboard_state.load_plot_data(item.name)
                dashboard_state._data[item.name] = data

        dashboard_state.apply_data()

    def on_add(self, ctx):
        if _can_edit(ctx):
            ctx.prompt(
                CONFIGURE_PLOT_URI,
                on_success=self.on_configure_plot,
            )

    def handle_plot_change(self, ctx, edit=False):
        result = ctx.params.get("result")
        p = _get_plotly_config_and_layout(result)
        plot_layout = p.get("layout", {})
        plot_config = p.get("config", {})
        plot_type = result.get("plot_type")
        code = result.get("code", None)
        update_on_change = result.get("update_on_change", None)
        with DashboardState(ctx) as dashboard_state:
            name = result.get("name", dashboard_state.get_next_item_id())
            item = DashboardPlotItem(
                name=name,
                type=plot_type,
                config={**plot_config, "scrollZoom": False},
                layout=plot_layout,
                raw_params=result,
                use_code=result.get("use_code", False),
                code=code,
                update_on_change=update_on_change,
                x_field=result.get("x_field", None),
                y_field=result.get("y_field", None),
                field=result.get("field", None),
                bins=result.get("bins", 10),
                order=result.get("order", "alphabetical"),
                reverse=result.get("reverse", False),
                limit=result.get("limit", None),
            )

            if edit:
                dashboard_state.edit_plot(item)
            else:
                dashboard_state.add_plot(item)

    def on_configure_plot(self, ctx):
        self.handle_plot_change(ctx)

    def on_edit_success(self, ctx):
        self.handle_plot_change(ctx, edit=True)

    def on_edit(self, ctx):
        plot_id = ctx.params.get("id")
        dashboard_state = DashboardState(ctx)
        item = dashboard_state.get_item(plot_id)
        if item is None:
            return

        if _can_edit(ctx):
            ctx.prompt(
                CONFIGURE_PLOT_URI,
                on_success=self.on_edit_success,
                params=item.to_configure_plot_params(),
            )

    def on_save_layout(self, ctx):
        rows = ctx.params.get("rows")
        items = ctx.params.get("items")
        cols = ctx.params.get("cols")
        auto_layout = ctx.params.get("auto_layout")
        ctx.panel.state.dashboard_config = {
            "rows": rows,
            "cols": cols,
            "items": items,
            "auto_layout": auto_layout,
        }

    def on_remove(self, ctx):
        if _can_edit(ctx):
            plot_id = ctx.params.get("id")
            with DashboardState(ctx) as dashboard_state:
                dashboard_state.remove_item(plot_id)

    def on_click_plot(self, ctx):
        plot_id = ctx.params.get("relative_path")
        dashboard_state = DashboardState(ctx)
        item = dashboard_state.get_item(plot_id)
        if item.use_code:
            return

        x_field = item.x_field
        y_field = item.y_field

        if (
            item.type == PlotType.CATEGORICAL_HISTOGRAM
            or item.type == PlotType.NUMERIC_HISTOGRAM
        ):
            if item.type == PlotType.CATEGORICAL_HISTOGRAM:
                view = None
                x_field = item.field
                x = ctx.params.get("x")

                view = _make_view_for_value(dashboard_state.view, x_field, x)
                if view is not None:
                    ctx.ops.set_view(view=view)

                return

            range = ctx.params.get("range")
            if range:
                min_val, max_val = range
                if _check_for_isoformat(min_val):
                    x_data = dashboard_state.load_plot_data(item.name)["x"]
                    x_datetime = [datetime.fromisoformat(x) for x in x_data]
                    curr_val = datetime.fromisoformat(min_val)
                    min_val, max_val = find_datetime_max_val(
                        x_datetime, curr_val
                    )
                view = _make_view_for_range(
                    dashboard_state.view, x_field, min_val, max_val
                )
                ctx.ops.set_view(view=view)

        if item.type == PlotType.SCATTER or item.type == PlotType.LINE:
            range = ctx.params.get("range")
            if range:
                x = ctx.params.get("x")
                y = ctx.params.get("y")
                filter = {}
                filter[x_field] = x
                filter[y_field] = y
                ctx.trigger(
                    "set_view",
                    dict(
                        view=[
                            {
                                "_cls": "fiftyone.core.stages.Match",
                                "kwargs": [["filter", filter]],
                            }
                        ]
                    ),
                )

        if item.type == PlotType.PIE:
            category = ctx.params.get("label")
            view = _make_view_for_value(
                dashboard_state.view, item.field, category
            )
            if view is not None:
                ctx.ops.set_view(view=view)

    def on_plot_select(self, ctx):
        plot_id = ctx.params.get("relative_path")
        dashboard_state = DashboardState(ctx)
        item = dashboard_state.get_item(plot_id)
        if item.use_code or item.type == PlotType.PIE:
            return

        if item.type == PlotType.SCATTER or item.type == PlotType.LINE:
            data = ctx.params.get("data")
            ids = [d.get("id") for d in data]
            if not ids:
                return

            matched_ids_view = ctx.view.select(ids)
            ctx.ops.set_view(view=matched_ids_view)

    def render_menu(self, ctx):
        menu = types.Object()
        return types.Property(menu)

    def render_dashboard(self, ctx, on_click_plot, on_plot_select):
        dashboard = types.Object()
        dashboard_state = DashboardState(ctx)
        for dashboard_item in dashboard_state.items:
            dashboard.add_property(
                dashboard_item.name,
                DashboardPlotProperty.from_item(
                    dashboard_item, on_click_plot, on_plot_select
                ),
            )

        can_edit = _can_edit(ctx)
        dashboard_view = types.DashboardView(
            on_add_item=self.on_add,
            on_remove_item=self.on_remove,
            on_edit_item=self.on_edit,
            on_save_layout=self.on_save_layout,
            allow_edit=can_edit,
            allow_remove=can_edit,
            allow_add=can_edit,
            width=100,
            height=100 if dashboard_state.is_empty else None,
            cta_title="Add a plot",
            cta_body="Add a new plot to the dashboard",
            cta_button_label="Add plot",
            **(ctx.panel.state.dashboard_config or {}),
        )
        return types.Property(dashboard, view=dashboard_view)

    def render(self, ctx):
        panel = types.Object()
        panel.add_property(
            "items",
            self.render_dashboard(
                ctx, self.on_click_plot, self.on_plot_select
            ),
        )
        return types.Property(panel, view=types.GridView(padding=0, gap=0))


class ConfigurePlot(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="configure_plot",
            label="Configure plot",
            dynamic=True,
            unlisted=True,
        )

    def get_number_field_choices(self, ctx):
        fields = types.Choices(space=6)
        paths = _get_fields_with_type(ctx.view, NUMERIC_TYPES)
        for field_path in paths:
            fields.add_choice(field_path, label=field_path)

        return fields

    def get_categorical_field_choices(self, ctx):
        fields = types.Choices(space=3)
        paths = _get_fields_with_type(ctx.view, CATEGORICAL_TYPES)
        for field_path in paths:
            fields.add_choice(field_path, label=field_path)

        return fields

    def create_axis_input(self, ctx, inputs, axis):
        axis_obj = types.Object()
        axis_obj.str(
            "title",
            default=None,
            label=f"{axis} axis title",
        )
        inputs.define_property(
            f"{axis}axis",
            axis_obj,
            label=f"{axis} axis",
        )

    def get_code_example(self, plot_type):
        examples = {
            "categorical_histogram": dedent(
                """
                import random
                categories = ['A', 'B', 'C', 'D', 'E']
                data = {
                    'x': random.choices(categories, k=100),
                }
            """
            ).strip(),
            "numeric_histogram": dedent(
                """
                import numpy as np
                data = {
                    'x': np.random.normal(size=1000),
                }
            """
            ).strip(),
            "line": dedent(
                """
                import numpy as np
                x = np.arange(0, 10, 0.1)
                y = np.sin(x)
                data = {
                    'x': x.tolist(),
                    'y': y.tolist(),
                }
            """
            ).strip(),
            "scatter": dedent(
                """
                import numpy as np
                x = np.random.rand(100)
                y = np.random.rand(100)
                data = {
                    'x': x.tolist(),
                    'y': y.tolist(),
                    'mode': 'markers'
                }
            """
            ).strip(),
            "pie": dedent(
                """
                data = {
                    'values': [33, 33, 33],
                    'labels': ['A', 'B', 'C'],
                }
            """
            ).strip(),
        }
        return examples.get(plot_type, "")

    def resolve_input(self, ctx):
        inputs = types.Object()
        plot_choices = types.Choices(label="Plot type")
        plot_choices.add_choice(
            "categorical_histogram",
            label="Categorical histogram",
            description="Displays the frequency of each category in a field",
        )
        plot_choices.add_choice(
            "numeric_histogram",
            label="Numeric histogram",
            description="Displays the distribution of a numeric field",
        )
        plot_choices.add_choice(
            "line",
            label="Line",
            description="Displays a line plot",
        )
        plot_choices.add_choice(
            "scatter",
            label="Scatter",
            description="Displays a scatter plot",
        )
        plot_choices.add_choice(
            "pie",
            label="Pie",
            description="Displays a pie chart",
        )

        plot_type = ctx.params.get("plot_type")

        inputs.enum(
            "plot_type",
            values=plot_choices.values(),
            view=plot_choices,
            required=True,
            description="Select the type of plot to create",
        )
        use_code = ctx.params.get("use_code")

        if plot_type:
            inputs.str(
                "plot_title",
                label="Plot title",
                description="A title to display above the plot",
            )
            inputs.bool(
                "use_code",
                default=False,
                label="Custom data source",
                description="Define a custom data source in Python",
            )

            if use_code:
                code_example = self.get_code_example(plot_type)
                inputs.str(
                    "code",
                    label="Code editor",
                    default=code_example,
                    view=types.CodeView(language="python", space=6),
                )
            else:
                number_fields = self.get_number_field_choices(ctx)
                categorical_fields = self.get_categorical_field_choices(ctx)

                if plot_type == "line" or plot_type == "scatter":
                    inputs.enum(
                        "y_field",
                        values=number_fields.values(),
                        view=number_fields,
                        required=True,
                        label="y data source",
                        description="The field to use to populate the y axis",
                    )
                    self.create_axis_input(ctx, inputs, "y")
                if plot_type != "pie" and plot_type != "categorical_histogram":
                    inputs.enum(
                        "x_field",
                        values=number_fields.values(),
                        view=number_fields,
                        required=True,
                        label="x data source",
                        description="The field to use to populate the x axis",
                    )
                    self.create_axis_input(ctx, inputs, "x")

                if plot_type == "categorical_histogram" or plot_type == "pie":
                    inputs.enum(
                        "field",
                        values=categorical_fields.values(),
                        view=categorical_fields,
                        required=True,
                        label="Category field",
                        description="The field to plot categories from",
                    )

            if plot_type == "numeric_histogram" and not use_code:
                inputs.int(
                    "bins",
                    default=10,
                    label="Number of bins",
                    view=types.View(space=6),
                    description=(
                        "The number of bins to split the histogram data into"
                    ),
                )

            if plot_type == "categorical_histogram":
                order_choices = types.Choices(label="Order", space=3)
                order_choices.add_choice(
                    "alphabetical",
                    label="Alphabetical",
                    description="Sort categories alphabetically",
                )
                order_choices.add_choice(
                    "frequency",
                    label="Frequency",
                    description="Sort categories by frequency",
                )
                inputs.enum(
                    "order",
                    values=order_choices.values(),
                    view=order_choices,
                    default="alphabetical",
                    label="Order",
                    description="The order to display the categories",
                    space=3,
                )
                inputs.int(
                    "limit",
                    default=None,
                    label="Limit bars",
                    view=types.View(space=3),
                    description="Optional max bars to display",
                    space=3,
                )
                inputs.bool(
                    "reverse",
                    default=False,
                    label="Reverse order",
                    description="Reverse the order of the categories",
                    view=types.View(space=3),
                )

            inputs.bool(
                "update_on_change",
                default=True,
                label="Update on view change",
                description=(
                    "Whether to automatically update the plot when the view "
                    "changes"
                ),
            )

            plotly_layout_and_config = _get_plotly_config_and_layout(
                ctx.params
            )
            preview_config = plotly_layout_and_config.get("config", {})
            preview_layout = plotly_layout_and_config.get("layout", {})
            item = DashboardPlotItem.from_dict(
                {
                    "name": "plot_preview",
                    "type": plot_type,
                    "config": preview_config,
                    "layout": preview_layout,
                    "use_code": ctx.params.get("use_code", False),
                    "code": ctx.params.get("code", None),
                    "x_field": ctx.params.get("x_field", None),
                    "y_field": ctx.params.get("y_field", None),
                    "field": ctx.params.get("field", None),
                    "bins": ctx.params.get("bins", 10),
                    "order": ctx.params.get("order", "alphabetical"),
                    "reverse": ctx.params.get("reverse", False),
                    "limit": ctx.params.get("limit", None),
                }
            )

            dashboard_state = DashboardState(ctx)
            if dashboard_state.can_load_data(item):
                preview_data = dashboard_state.load_plot_data_for_item(item)
                preview_container = inputs.grid(
                    "grid", height="400px", width="100%"
                )
                preview_height = "600px" if plot_type == "pie" else "300px"
                preview_container.plot(
                    "plot_preview",
                    label="Plot preview",
                    config=preview_config,
                    layout=preview_layout,
                    data=preview_data,
                    height=preview_height,
                    width="600px",
                )

        is_edit = ctx.params.get("name", None) is not None
        submit_button_label = "Update plot" if is_edit else "Create plot"
        prompt = types.PromptView(submit_button_label=submit_button_label)

        return types.Property(inputs, view=prompt)

    def execute(self, ctx):
        plot_config = ctx.params
        plot_config.pop("panel_state")
        plotly_layout_and_config = _get_plotly_config_and_layout(plot_config)
        return {**ctx.params, **plotly_layout_and_config}


class DashboardPlotProperty(types.Property):
    def __init__(self, item, on_click_plot=None, on_plot_select=None):
        name = item.name
        label = item.label
        plot_config = item.config
        plot_layout = item.layout
        x_field = item.x_field
        y_field = item.y_field
        type = types.Object()
        view = types.PlotlyView(
            config=plot_config,
            layout=plot_layout,
            on_click=on_click_plot,
            on_selected=on_plot_select,
            x_data_source=x_field,
            y_data_source=y_field,
        )
        super().__init__(type, view=view)
        self.name = name
        self.label = label

    @staticmethod
    def from_item(item, on_click_plot, on_plot_select):
        return DashboardPlotProperty(
            item, on_click_plot=on_click_plot, on_plot_select=on_plot_select
        )


class DashboardPlotItem(object):
    def __init__(
        self,
        name,
        type,
        config,
        layout,
        raw_params=None,
        use_code=False,
        code=None,
        update_on_change=None,
        x_field=None,
        y_field=None,
        field=None,
        bins=10,
        order="alphabetical",
        reverse=False,
        limit=None,
    ):
        self.name = name
        self.type = PlotType(type)
        self.raw_params = raw_params
        self.config = config
        self.layout = layout
        self.use_code = use_code
        self.code = code
        self.update_on_change = update_on_change
        self.x_field = x_field
        self.y_field = y_field
        self.field = field
        self.bins = bins
        self.order = order
        self.reverse = reverse
        self.limit = limit

    @staticmethod
    def from_dict(data):
        return DashboardPlotItem(
            data.get("name"),
            data.get("type"),
            data.get("config"),
            data.get("layout"),
            data.get("raw_params", None),
            data.get("use_code", False),
            data.get("code"),
            data.get("update_on_change"),
            data.get("x_field", None),
            data.get("y_field", None),
            data.get("field", None),
            data.get("bins", 10),
            data.get("order", "alphabetical"),
            data.get("reverse", False),
            data.get("limit", None),
        )

    @property
    def label(self):
        raw_params = self.raw_params or {}
        return raw_params.get("plot_title", self.name)

    def to_configure_plot_params(self):
        return {**self.raw_params, "name": self.name}

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "layout": self.layout,
            "raw_params": self.raw_params,
            "use_code": self.use_code,
            "code": self.code,
            "update_on_change": self.update_on_change,
            "x_field": self.x_field,
            "y_field": self.y_field,
            "field": self.field,
            "bins": self.bins,
            "order": self.order,
            "reverse": self.reverse,
            "limit": self.limit,
        }


class DashboardState(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.panel = ctx.panel
        self._data = {}
        self._items = {}

        items = ctx.panel.get_state("items_config")
        if items:
            for key, item in items.items():
                self._items[key] = DashboardPlotItem.from_dict(item)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.apply_state()

    @property
    def is_empty(self):
        return len(self._items) == 0

    @property
    def view(self):
        return self.ctx.view

    @property
    def items(self):
        return self._items.values()

    @property
    def item_count(self):
        return len(self._items)

    def items_as_dict(self):
        return {k: v.to_dict() for k, v in self._items.items()}

    def apply_state(self):
        self.ctx.panel.state.items = None
        items_dict = self.items_as_dict()
        self.panel.set_state("items_config", items_dict)

    def apply_data(self):
        self.ctx.panel.state.items = None
        data_paths_dict = {f"items.{k}": v for k, v in self._data.items()}
        self.panel.set_data(data_paths_dict)

    def get_item(self, item_id):
        return self._items.get(item_id, None)

    def remove_item(self, item_id):
        # @todo properly handle clearing of state/data
        self._items.pop(item_id)

    def clear_items(self):
        self._items = {}

    def get_next_item_id(self):
        return f"plot_{random.randint(0, 1000)}"

    def add_plot(self, item):
        self._items[item.name] = item

        data = self.load_plot_data_for_item(item)

        self._data[item.name] = data
        self.apply_data()

    def edit_plot(self, item):
        self._items[item.name] = item

        data = self.load_plot_data_for_item(item)

        self._data[item.name] = data
        self.apply_data()

    def load_plot_data(self, plot_id):
        item = self.get_item(plot_id)
        if item is None:
            return {}

        data = self.load_plot_data_for_item(item)
        if isinstance(data, dict):
            return data

        return {}

    def load_plot_data_for_item(self, item):
        fo_orange = "rgb(255, 109, 5)"
        bar_color = {"marker": {"color": fo_orange}}
        pie_color = {
            "marker": {
                "colors": [
                    "rgb(255, 109, 5)",
                    "rgb(255, 109, 5)",
                    "rgb(255, 109, 5)",
                ]
            }
        }

        if item.use_code:
            data = self.load_data_from_code(item.code, item.type)
        elif item.type == PlotType.CATEGORICAL_HISTOGRAM:
            data = self.load_categorical_histogram_data(item)
        elif item.type == PlotType.NUMERIC_HISTOGRAM:
            data = self.load_numeric_histogram_data(item)
        elif item.type == PlotType.SCATTER:
            data = self.load_scatter_data(item)
        elif item.type == PlotType.LINE:
            data = self.load_line_data(item)
        elif item.type == PlotType.PIE:
            data = self.load_pie_data(item)

        if isinstance(data, dict):
            plot_data_type = data.get("type", None)
            if plot_data_type == "pie":
                # pie_color = {
                #     "marker": {
                #         "colors": fo.app_config.color_pool[:len(data['labels'])]
                #     }
                # }
                # data.update(pie_color)
                pass
            else:
                data.update(bar_color)

            return {"name": item.label, **data}
        return {}

    def load_all_plot_data(self):
        for item in self.items:
            data = self.load_plot_data(item.name)
            self._data[item.name] = data

        self.apply_data()

    def load_categorical_histogram_data(self, item):
        field = item.field
        if not field:
            return {}

        counts = self.view.count_values(field)
        raw_keys = list(counts.keys())
        keys = [str(k) for k in raw_keys]

        if item.order == "alphabetical":
            sorted_items = sorted(
                zip(keys, counts.values()),
                key=lambda x: x[0],
                reverse=item.reverse,
            )
        elif item.order == "frequency":
            sorted_items = sorted(
                zip(keys, counts.values()),
                key=lambda x: x[1],
                reverse=not item.reverse,
            )

        if item.limit:
            sorted_items = sorted_items[: item.limit]

        if len(sorted_items) == 0:
            return {"x": [], "y": [], "type": "bar"}

        keys, values = zip(*sorted_items)

        histogram_data = {"x": keys, "y": values, "type": "bar"}

        return histogram_data

    def load_numeric_histogram_data(self, item):
        x = item.x_field
        if not x:
            return {}

        bins = item.bins
        x_values = self.view.distinct(x)
        if len(x_values) == 1 and isinstance(x_values[0], datetime):
            counts = [len(self.view)] + [0] * (bins - 1)
            edges = [
                x_values[0] + timedelta(milliseconds=i) for i in range(bins)
            ]
        else:
            counts, edges, _ = self.view.histogram_values(x, bins=bins)

        counts = np.asarray(counts)
        edges = np.asarray(edges)

        left_edges = edges[:-1]
        widths = edges[1:] - edges[:-1]

        if len(left_edges) > 0:
            if isinstance(left_edges[0], datetime):
                left_edges = [edge.isoformat() for edge in left_edges]
                widths = None  # widths set to None to avoid thin unclickable bars with datetime field
        else:
            left_edges = left_edges.tolist()
            widths = widths.tolist()

        histogram_data = {
            "x": left_edges,
            "y": counts.tolist(),
            "type": "bar",
        }

        # Include widths only if they are numerical
        if widths is not None:
            histogram_data["width"] = widths

        return histogram_data

    def load_scatter_data(self, item):
        x = self.view.values(F(item.x_field))
        y = self.view.values(F(item.y_field))
        if not x or not y:
            return {}

        ids = self.view.values("id")

        scatter_data = {
            "x": x,
            "y": y,
            "ids": ids,
            "type": "scatter",
            "mode": "markers",
        }

        return scatter_data

    def load_line_data(self, item):
        if item.x_field is None or item.y_field is None:
            return {}

        x = self.view.values(F(item.x_field))
        y = self.view.values(F(item.y_field))

        line_data = {"x": x, "y": y, "type": "line"}

        return line_data

    def load_pie_data(self, item):
        field = item.field
        if not field:
            return {}

        counts = self.view.count_values(field)
        values = list(counts.values())
        keys = list(counts.keys())
        total = np.sum(values)
        factor = 100.0 / total
        factored_values = [v * factor for v in values]

        pie_data = {"values": factored_values, "labels": keys, "type": "pie"}

        if len(values) > 10:
            pie_data["textinfo"] = "none"

        return pie_data

    def load_data_from_code(self, code, plot_type):
        if not code:
            return {}

        local_vars = {}
        try:
            exec(code, {"ctx": self.ctx}, local_vars)
            data = local_vars.get("data", {})
            data["type"] = _get_plotly_plot_type(plot_type).value
            return data
        except Exception as e:
            return {}

    def can_load_data(self, item):
        if item.code:
            return True
        if item.type == PlotType.CATEGORICAL_HISTOGRAM:
            return item.field is not None
        elif item.type == PlotType.NUMERIC_HISTOGRAM:
            return item.x_field is not None
        elif item.type == PlotType.SCATTER:
            return item.x_field is not None and item.y_field is not None
        elif item.type == PlotType.LINE:
            return item.x_field is not None and item.y_field is not None
        elif item.type == PlotType.PIE:
            return item.field is not None


def _can_edit(ctx):
    if ctx.user is None:
        return True

    ds_perm = str(ctx.user.dataset_permission).upper()
    return ds_perm in ["EDIT", "MANAGE", "ADMIN"]


def _get_plotly_plot_type(plot_type):
    return {
        PlotType.CATEGORICAL_HISTOGRAM: PlotlyPlotType.BAR,
        PlotType.NUMERIC_HISTOGRAM: PlotlyPlotType.BAR,
        PlotType.LINE: PlotlyPlotType.LINE,
        PlotType.SCATTER: PlotlyPlotType.SCATTER,
        PlotType.PIE: PlotlyPlotType.PIE,
    }.get(plot_type)


def _get_plotly_config_and_layout(plot_config):
    layout = {}
    title = None
    if plot_config.get("plot_title"):
        title = plot_config.get("plot_title")
    if plot_config.get("color"):
        layout["marker"] = {"color": plot_config["color"].get("hex")}
    if plot_config.get("xaxis"):
        layout["xaxis"] = plot_config.get("xaxis")
    if plot_config.get("yaxis"):
        layout["yaxis"] = plot_config.get("yaxis")
    if plot_config.get("plot_type") == "numeric_histogram":
        layout["bargap"] = 0
        layout["bargroupgap"] = 0
    if plot_config.get("plot_type") == "categorical_histogram":
        xaxis = plot_config.get("xaxis", {})
        layout["xaxis"] = {
            "type": "category",
            **xaxis,
        }

    return {"config": {}, "layout": layout, "title": title}


def _get_fields_with_type(dataset, field_types, root=None):
    schema = dataset.get_field_schema(flat=True)
    paths = []
    for path, field in schema.items():
        if root is not None and not path.startswith(root + "."):
            continue

        if isinstance(field, field_types) or (
            isinstance(field, fo.ListField)
            and isinstance(field.field, field_types)
        ):
            paths.append(path)

    return paths


def _make_view_for_value(sample_collection, path, value):
    """Returns a view into the given `sample_collection` that matches the given
    `value` within the given `path`.

    Supports label fields, list fields, and a combination of both.
    """
    root, leaf = _parse_path(sample_collection, path)
    is_label_field = _is_field_type(sample_collection, root, fo.Label)
    is_list_field = _is_field_type(sample_collection, path, fo.ListField)

    if is_label_field:
        if is_list_field:
            expr = F(leaf).exists() & F(leaf).contains(value)
        else:
            expr = F(leaf) == value

        return sample_collection.filter_labels(root, expr)

    if is_list_field:
        expr = F(path).exists() & F(path).contains(value)
    else:
        expr = F(path) == value

    return sample_collection.match(expr)


def _make_view_for_range(sample_collection, path, min_val, max_val):
    expr = (F(path) >= min_val) & (F(path) <= max_val)
    return sample_collection.match(expr)


def _is_field_type(sample_collection, path, field_or_type):
    field = sample_collection.get_field(path)

    if issubclass(field_or_type, fo.Field):
        return isinstance(field, field_or_type)

    return isinstance(field, fo.EmbeddedDocumentField) and issubclass(
        field.document_type, field_or_type
    )


def _parse_path(sample_collection, path):
    if "." not in path:
        return path, None

    chunks = path.split(".")
    root = chunks[0]
    leaf = chunks[-1]

    # Handle dynamic documents
    idx = 0
    while _is_field_type(
        sample_collection, root, fo.EmbeddedDocumentField
    ) and not _is_field_type(sample_collection, root, fo.Label):
        idx += 1
        root += "." + chunks[idx]

    return root, leaf


def _check_for_isoformat(value):
    try:
        datetime.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def find_datetime_max_val(x_datetime, min_val):
    if min_val < x_datetime[0]:
        return min_val, x_datetime[0]
    if min_val >= x_datetime[-1]:
        return x_datetime[-1], min_val
    for i in range(len(x_datetime) - 1):
        if x_datetime[i] <= min_val < x_datetime[i + 1]:
            return x_datetime[i], x_datetime[i + 1]


def register(p):
    p.register(DashboardPanel)
    p.register(ConfigurePlot)
