"""
Custom Dashboards.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import enum
import numpy as np
import random
from textwrap import dedent

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.types as fot
import fiftyone.core.fields as fof
from fiftyone import ViewField as F

# Set CAN_EDIT to True for testing purposes
CAN_EDIT = True

class PlotlyPlotType(enum.Enum):
    bar = 'bar'
    scatter = 'scatter'
    line = 'line'
    pie = 'pie'

class PlotType(enum.Enum):
    categorical_histogram = 'categorical_histogram'
    numeric_histogram = 'numeric_histogram'
    line = 'line'
    scatter = 'scatter'
    pie = 'pie'

NUMERIC_TYPES = (
    fof.IntField,
    fof.FloatField,
)

CATEGORICAL_TYPES = (
    fof.StringField,
    fof.BooleanField,
    fof.IntField,
    fof.FloatField,
)

def get_plotly_plot_type(plot_type):
    if plot_type == PlotType.categorical_histogram:
        return PlotlyPlotType.bar
    elif plot_type == PlotType.numeric_histogram:
        return PlotlyPlotType.bar
    elif plot_type == PlotType.line:
        return PlotlyPlotType.line
    elif plot_type == PlotType.scatter:
        return PlotlyPlotType.scatter
    elif plot_type == PlotType.pie:
        return PlotlyPlotType.pie

def get_plotly_config_and_layout(plot_config):
    config = {}
    layout = {}
    if plot_config.get('plot_title'):
        layout['title'] = plot_config.get('plot_title')
    if plot_config.get('color'):
        color = plot_config.get('color')
        layout['marker'] = {'color': color.get('hex')}
    if plot_config.get('xaxis'):
        layout['xaxis'] = plot_config.get('xaxis')
    if plot_config.get('yaxis'):
        layout['yaxis'] = plot_config.get('yaxis')
    if plot_config.get('plot_type') == 'numeric_histogram':
        layout['bargap'] = 0
        layout['bargroupgap'] = 0
    return {
        'config': config,
        'layout': layout
    }

requires_x = [PlotType.scatter, PlotType.line, PlotType.numeric_histogram]
requires_y = [PlotType.scatter, PlotType.line]

def get_root(dataset, path):
    root = None
    schema = dataset.get_field_schema(flat=True)
    for _path, field in schema.items():
        if path.startswith(_path + ".") and isinstance(field. fo.ListField):
            root = _path

    return root

def get_fields_with_type(dataset, field_types, root=None):
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

#
# Types
#

class PlotDefinition(object):
    def __init__(self, plot_type, layout={}, config={}, sources={}, code=None):
        self.plot_type = plot_type
        self.layout = layout
        self.config = config
        self.x_source = sources.get('x', None)
        self.y_source = sources.get('y', None)
        self.z_source = sources.get('z', None)
        self.code = code

    @staticmethod
    def requires_source(cls, plot_type, dim):
        if dim == 'x':
            return plot_type in requires_x
        if dim == 'y':
            return plot_type in requires_y


class DashboardPlotProperty(types.Property):
    def __init__(self, name, label, plot_config={}, plot_layout={}, on_click_plot=None):
        type = types.Object()
        view = types.PlotlyView(
            config=plot_config,
            layout=plot_layout,
            on_click=on_click_plot
        )
        super().__init__(type, view=view)
        self.name = name
        self.label = label

    @staticmethod
    def from_item(item, on_click_plot):
        return DashboardPlotProperty(
            item.name,
            item.label,
            plot_config=item.config,
            plot_layout=item.layout,
            on_click_plot=on_click_plot
        )


class DashboardPlotItem(object):
    def __init__(self, name, type, config, layout, use_code=False, code=None, update_on_change=None, x_field=None, y_field=None, field=None, bins=10):
        self.name = name
        self.type = PlotType(type)
        self.config = config
        self.layout = layout
        self.use_code = use_code
        self.code = code
        self.update_on_change = update_on_change
        self.x_field = x_field
        self.y_field = y_field
        self.field = field
        self.bins = bins

    @staticmethod
    def from_dict(data):
        return DashboardPlotItem(
            data.get('name'),
            data.get('type'),
            data.get('config'),
            data.get('layout'),
            data.get('use_code', False),
            data.get('code'),
            data.get('update_on_change'),
            data.get('x_field', None),
            data.get('y_field', None),
            data.get('field', None),
            data.get('bins', 10)
        )
    
    @property
    def label(self):
        return self.config.get('title', self.name)
    
    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type.value,
            'config': self.config,
            'layout': self.layout,
            'use_code': self.use_code,
            'code': self.code,
            'update_on_change': self.update_on_change,
            'x_field': self.x_field,
            'y_field': self.y_field,
            'field': self.field,
            'bins': self.bins
        }


class DashboardState(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.panel = ctx.panel
        self._items = {}
        self._data = {}
        items = ctx.panel.get_state("items_config")
        if items:
            for key, item in items.items():
                self._items[key] = DashboardPlotItem.from_dict(item)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.apply_state()
        if exc_type is not None:
            print(f"An exception occurred: {exc_type}, {exc_value}")
        return True
    
    @property
    def items(self):
        return self._items.values()
    
    @property
    def item_count(self):
        return len(self._items)

    def items_as_dict(self):
        return {k: v.to_dict() for k, v in self._items.items()}
    
    def apply_state(self):
        items_dict = self.items_as_dict()
        self.panel.set_state("items_config", items_dict)

    def apply_data(self):
        print('applying data', self._data)
        data_paths_dict = {f"items.{k}": v for k, v in self._data.items()}
        self.panel.batch_set_data(data_paths_dict)

    def get_item(self, item_id):
        return self._items.get(item_id, None)
    
    def remove_item(self, item_id):
        self._items.pop(item_id)
        # TODO: properly handle clearing of state/data

    def clear_items(self):
        self._items = {}
    
    def get_next_item_id(self):
        return f"plot_{random.randint(0, 1000)}"

    def add_plot(self, item):
        self._items[item.name] = item
        print('loading plot data', item.to_dict())
        data = self.load_plot_data_for_item(item)
        print("data", data)
        self._data[item.name] = data
        self.apply_data()
            
    def load_plot_data(self, plot_id):
        item = self.get_item(plot_id)
        if item is None:
            return {}
        return self.load_plot_data_for_item(item)
    
    def load_plot_data_for_item(self, item):
        if item.use_code:
            return self.load_data_from_code(item.code, item.type)
        if item.type == PlotType.categorical_histogram:
            return self.load_categorical_histogram_data(item)
        elif item.type == PlotType.numeric_histogram:
            return self.load_numeric_histogram_data(item)
        elif item.type == PlotType.scatter:
            return self.load_scatter_data(item)
        elif item.type == PlotType.line:
            return self.load_line_data(item)
        elif item.type == PlotType.pie:
            return self.load_pie_data(item)
    
    def load_all_plot_data(self):
        for item in self.items:
            data = self.load_plot_data(item.name)
            self._data[item.name] = data
        self.apply_data()

    def load_categorical_histogram_data(self, item):
        field = item.field
        if not field:
            return {}
        counts = self.ctx.dataset.count_values(field)
        
        histogram_data = {
            'x': list(counts.keys()),
            'y': list(counts.values()),
            'type': 'bar'
        }

        print("histogram_data", histogram_data)
        
        return histogram_data

    def load_numeric_histogram_data(self, item):
        x = item.x_field
        bins = item.bins

        if not x:
            return {}
        
        counts, edges, other = self.ctx.dataset.histogram_values(
            x,
            bins=bins,
        )
        
        counts = np.asarray(counts)
        edges = np.asarray(edges)
        
        left_edges = edges[:-1]
        widths = edges[1:] - edges[:-1]
        
        histogram_data = {
            'x': left_edges.tolist(),
            'y': counts.tolist(),
            'type': 'bar',
            'width': widths.tolist()
        }
        
        return histogram_data

    def load_scatter_data(self, item):
        x = self.ctx.dataset.values(F(item.x_field))
        y = self.ctx.dataset.values(F(item.y_field))
        
        if not x or not y:
            return {}

        scatter_data = {
            'x': x,
            'y': y,
            'type': 'scatter',
            'mode': 'markers'
        }
        
        return scatter_data

    def load_line_data(self, item):
        if item.x_field is None or item.y_field is None:
            return {}
        
        x = self.ctx.dataset.values(F(item.x_field))
        y = self.ctx.dataset.values(F(item.y_field))
        
        line_data = {
            'x': x,
            'y': y,
            'type': 'line'
        }
        
        return line_data

    def load_pie_data(self, item):
        field = item.config.get('field')

        if not field:
            return {}

        values = self.ctx.dataset.count_values(field)

        pie_data = {
            'values': list(values.values()),
            'labels': list(values.keys()),
            'type': 'pie',
            'name': item.config.get('title', 'Pie Chart')
        }
        
        return pie_data

    def load_data_from_code(self, code, plot_type):
        if not code:
            return {}
        local_vars = {}
        try:
            exec(code, {'ctx': self.ctx}, local_vars)
            data = local_vars.get('data', {})
            data['type'] = get_plotly_plot_type(plot_type).value
            print("data", data)
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return {}
    
    def can_load_data(self, item):
        if item.code:
            return True
        if item.type == PlotType.categorical_histogram:
            return item.field is not None
        elif item.type == PlotType.numeric_histogram:
            return item.x_field is not None
        elif item.type == PlotType.scatter:
            return item.x_field is not None and item.y_field is not None
        elif item.type == PlotType.line:
            return item.x_field is not None and item.y_field is not None
        elif item.type == PlotType.pie:
            return item.field is not None

class CustomDashboard(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="custom_dashboard",
            label="Custom Dashboard",
            description="A custom dashboard"
        )
    
    #
    # Events
    #

    def on_load(self, ctx):
        dashboard_state = DashboardState(ctx)
        dashboard_state.load_all_plot_data()

    def on_add(self, ctx):
        if CAN_EDIT:
            ctx.prompt("@voxel51/custom_dashboard/configure_plot", on_success=self.on_configure_plot)

    def on_configure_plot(self, ctx):
        result = ctx.params.get("result")
        p = get_plotly_config_and_layout(result)
        plot_layout = p.get("layout", {})
        plot_config = p.get("config", {})
        plot_type = result.get("plot_type")
        code = result.get("code", None)
        update_on_change = result.get("update_on_change", None)
        with DashboardState(ctx) as dashboard_state:
            item = DashboardPlotItem(
                name=dashboard_state.get_next_item_id(),
                type=plot_type,
                config=plot_config,
                layout=plot_layout,
                use_code=result.get('use_code', False),
                code=code,
                update_on_change=update_on_change,
                x_field=result.get('x_field', None),
                y_field=result.get('y_field', None),
                field=result.get('field', None),
                bins=result.get('bins', 10)
            )
            dashboard_state.add_plot(item)

    def on_remove(self, ctx):
        plot_id = ctx.params.get("id")
        with DashboardState(ctx) as dashboard_state:
            dashboard_state.remove_item(plot_id)

    def on_click_plot(self, ctx):
        print("click", ctx.params)
        plot_type = ctx.params.get("data", {}).get("config", {}).get("plot_type")
        if plot_type == 'categorical_histogram' or plot_type == 'numeric_histogram':
            print(f"{plot_type} clicked")

    #
    # Load plot data
    #     

    def load_data(self, ctx):
        pass

    #
    # Render Properties
    #

    def render_menu(self, ctx):
        menu = types.Object()
        # menu.btn('btn', label='Button')
        return types.Property(menu)
    
    def render_dashboard(self, ctx, on_click_plot):
        dashboard = types.Object()
        dashboard_state = DashboardState(ctx)
        for dashboard_item in dashboard_state.items:
            dashboard.add_property(
                dashboard_item.name,
                DashboardPlotProperty.from_item(dashboard_item, on_click_plot)
            )
        dashboard_view = types.DashboardView(
            on_add_item=self.on_add,
            on_remove_item=self.on_remove
        )
        return types.Property(dashboard, view=dashboard_view)

    def render(self, ctx):
        panel = types.Object()
        panel.add_property('menu', self.render_menu(ctx))
        panel.add_property('items', self.render_dashboard(ctx, self.on_click_plot))
        return types.Property(panel)

#
# Operators
#

class ConfigurePlot(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="configure_plot",
            label="Configure Plot",
            description="Configure a plot",
            dynamic=True,
            unlisted=True
        )
    
    def get_number_field_choices(self, ctx):
        fields = types.Choices(space=6)
        paths = get_fields_with_type(ctx.dataset, NUMERIC_TYPES)
        for field_path in paths:
            fields.add_choice(field_path, label=field_path)
        return fields

    def get_categorical_field_choices(self, ctx):
        fields = types.Choices(space=6)
        paths = get_fields_with_type(ctx.dataset, CATEGORICAL_TYPES)
        for field_path in paths:
            fields.add_choice(field_path, label=field_path)
        return fields

    def create_axis_input(self, ctx, inputs, axis):
        axis_obj = types.Object()
        axis_bool_view = types.CheckboxView(space=3)
        axis_obj.str('title', default=None, label=f"Title")
        axis_obj.bool('showgrid', default=True, label="Show Grid", view=axis_bool_view)
        axis_obj.bool('zeroline', default=False, label="Show Zero Line", view=axis_bool_view)
        axis_obj.bool('showline', default=True, label="Show Line", view=axis_bool_view)
        axis_obj.bool('mirror', default=False, label="Mirror", view=axis_bool_view)
        axis_obj.bool('autotick', default=True, label="Auto Tick", view=axis_bool_view)
        axis_obj.bool('showticklabels', default=True, label="Show Tick Labels", view=axis_bool_view)
        axis_obj.bool('showspikes', default=False, label="Show Spikes", view=axis_bool_view)

        scale_choices = types.Choices()
        scale_choices.add_choice("linear", label="Linear")
        scale_choices.add_choice("log", label="Log")
        scale_choices.add_choice("date", label="Date")
        scale_choices.add_choice("category", label="Category")
        axis_obj.enum('type', values=scale_choices.values(), view=scale_choices, default="linear", label="Scale Type")

        axis_obj.float('tickangle', default=0, label="Tick Angle")
        axis_obj.str('tickformat', default=None, label="Tick Format", view=types.View(space=3))

        # Range settings
        axis_obj.bool('autorange', default=True, label="Auto Range", view=axis_bool_view)
        inputs.define_property(f"{axis}axis", axis_obj, label=f"{axis.capitalize()} Axis")

    def get_code_example(self, plot_type):
        if plot_type == 'categorical_histogram':
            return dedent("""
                import random
                categories = ['A', 'B', 'C', 'D', 'E']
                data = {
                    'x': random.choices(categories, k=100),
                }
            """).strip()
        elif plot_type == 'numeric_histogram':
            return dedent("""
                import numpy as np
                data = {
                    'x': np.random.normal(size=1000),
                }
            """).strip()
        elif plot_type == 'line':
            return dedent("""
                import numpy as np
                x = np.arange(0, 10, 0.1)
                y = np.sin(x)
                data = {
                    'x': x.tolist(),
                    'y': y.tolist(),
                }
            """).strip()
        elif plot_type == 'scatter':
            return dedent("""
                import numpy as np
                x = np.random.rand(100)
                y = np.random.rand(100)
                data = {
                    'x': x.tolist(),
                    'y': y.tolist(),
                    'mode': 'markers'
                }
            """).strip()
        elif plot_type == 'pie':
            return dedent("""
                data = {
                    'values': [33, 33, 33],
                    'labels': ['A', 'B', 'C'],
                }
            """).strip()

    def resolve_input(self, ctx):
        prompt = types.PromptView(submit_button_label="Create Plot")
        inputs = types.Object()
        plot_choices = types.Choices(label="Plot Type")
        plot_choices.add_choice("categorical_histogram", label="Categorical Histogram")
        plot_choices.add_choice("numeric_histogram", label="Numeric Histogram")
        plot_choices.add_choice("line", label="Line")
        plot_choices.add_choice("scatter", label="Scatter")
        plot_choices.add_choice("pie", label="Pie")

        plot_type = ctx.params.get('plot_type')

        inputs.enum('plot_type', values=plot_choices.values(), view=plot_choices, required=True)
        use_code = ctx.params.get('use_code')

        if plot_type:
            inputs.str('plot_title', label='Plot Title', description='Displayed above the plot')
            inputs.bool('use_code', default=False, label="Custom Python Data Source", description="Use python to populate plot data")

            if use_code:
                code_example = self.get_code_example(plot_type)
                inputs.str('code', label='Code Editor', default=code_example, view=types.CodeView(language="python", space=6))
            else:
                number_fields = self.get_number_field_choices(ctx)
                categorical_fields = self.get_categorical_field_choices(ctx)

                if plot_type == 'line' or plot_type == 'scatter':
                    inputs.enum('y_field', values=number_fields.values(), view=number_fields, required=True, label="Y Data Source")
                    self.create_axis_input(ctx, inputs, 'y')
                if plot_type != 'pie' and plot_type != 'categorical_histogram':
                    inputs.enum('x_field', values=number_fields.values(), view=number_fields, required=True, label="X Data Source")
                    self.create_axis_input(ctx, inputs, 'x')

                if plot_type == 'categorical_histogram':
                    inputs.enum('field', values=categorical_fields.values(), view=categorical_fields, required=True, label="Category Field")

            if plot_type == 'numeric_histogram':
                inputs.int('bins', default=10, label="Number of Bins", view=types.View(space=6))
            
            update_choices = types.Choices()
            update_choices.add_choice("dataset", label="Dataset Change")
            update_choices.add_choice("view", label="View Change")
            update_choices.add_choice("none", label="Neither")
            inputs.enum('update_on_change', values=update_choices.values(), view=update_choices, default="none", label="Update On Change")
            
            # plot preview
            plotly_layout_and_config = get_plotly_config_and_layout(ctx.params)
            preview_config = plotly_layout_and_config.get('config', {})
            preview_layout = plotly_layout_and_config.get('layout', {})
            item = DashboardPlotItem.from_dict({
                'name': 'plot_preview',
                'type': plot_type,
                'config': preview_config,
                'layout': preview_layout,
                'use_code': ctx.params.get('use_code', False),
                'code': ctx.params.get('code', None),
                'x_field': ctx.params.get('x_field', None),
                'y_field': ctx.params.get('y_field', None),
                'field': ctx.params.get('field', None),
                'bins': ctx.params.get('bins', 10)
            })
            preview_sx = {
                'height': "300px"
            }
            db = DashboardState(ctx)
            if db.can_load_data(item):
                preview_data = db.load_plot_data_for_item(item)
                inputs.plot('plot_preview', label='Plot Preview', config=preview_config, layout=preview_layout, data=preview_data, sx=preview_sx)

        return types.Property(inputs, view=prompt)
    
    def execute(self, ctx):
        plot_config = ctx.params
        plot_config.pop('panel_state') # todo: remove this and panel_state from params
        plotly_layout_and_config = get_plotly_config_and_layout(plot_config)
        return {
            **ctx.params,
            **plotly_layout_and_config
        }

def register(p):
    p.register(ConfigurePlot)
    p.register(CustomDashboard)
