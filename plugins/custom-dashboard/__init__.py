"""
Custom Dashboards.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import enum
import numpy as np
import random

import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.types as fot
import fiftyone.core.fields as fof
from fiftyone import ViewField as F


class PlotType(enum.Enum):
    histogram = 'histogram'
    line = 'line'
    scatter = 'scatter'
    heatmap = 'heatmap'


requires_x = [PlotType.scatter, PlotType.line]
requires_y = [PlotType.scatter, PlotType.line]
requires_z = [PlotType.heatmap]

#
# Types
#

class PlotDefinition(object):
    def __init__(self, plot_type, layout={}, config={}, sources={}):
        self.plot_type = plot_type
        self.layout = layout
        self.config = config
        self.x_source = sources.get('x', None)
        self.y_source = sources.get('y', None)
        self.z_source = sources.get('z', None)

    @staticmethod
    def requires_source(cls, plot_type, dim):
        if dim == 'x':
            return plot_type in requires_x
        if dim == 'y':
            return plot_type in requires_y
        if dim == 'z':
            return plot_type in requires_z


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
    def __init__(self, name, type, config, layout):
        self.name = name
        self.type = PlotType(type)
        self.config = config
        self.layout = layout

    @staticmethod
    def from_dict(cls, data):
        return DashboardPlotItem(
            data.get('name'),
            data.get('type'),
            data.get('config'),
            data.get('layout')
        )
    
    @property
    def label(self):
        return self.config.get('title', self.name)
    
    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type.value,
            'config': self.config,
            'layout': self.layout
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
                self._items[key] = DashboardPlotItem.from_dict(self, item)

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
    
    def add_plot(self, plot_type, plot_config={}, plot_layout={}):
        item_id = f"plot_{random.randint(0, 1000)}"
        item_path = f"items.{item_id}"
        item = DashboardPlotItem(
            item_id,
            plot_type,
            plot_config,
            plot_layout
        )
        self._items[item_id] = item
        data = self.load_plot_data(item_id)
        print("data", data)
        self._data[item_id] = data
        self.apply_data()
            
    def load_plot_data(self, plot_id):
        item = self.get_item(plot_id)
        if item:
            if item.type == PlotType.histogram:
                return self.load_histogram_data(item)
    
    def load_all_plot_data(self):
        for item in self.items:
            data = self.load_plot_data(item.name)
            self._data[item.name] = data
        self.apply_data()

    def load_histogram_data(self, item):
        x = item.config.get('x_field')
        bins = item.config.get('bins', 10)
        
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
            'width': widths.tolist(),
            'name': item.config.get('title', 'Histogram'),
            'marker': {
                'color': item.config.get('color', 'blue')
            }
        }
        
        return histogram_data


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
        ctx.prompt("@voxel51/custom_dashboard/configure_plot", on_success=self.on_configure_plot)

    def on_configure_plot(self, ctx):
        result = ctx.params.get("result")
        plot_config = result.get("plot_config", {})
        print("plot_config", plot_config)
        plot_layout = plot_config.get("layout", {})
        plot_type = plot_config.get("plot_type")
        with DashboardState(ctx) as dashboard_state:
            dashboard_state.add_plot(plot_type, plot_config, plot_layout)

    def on_remove(self, ctx):
        plot_id = ctx.params.get("id")
        with DashboardState(ctx) as dashboard_state:
            dashboard_state.remove_item(plot_id)

    def on_click_plot(self, ctx):
        print("click", ctx.params)
        plot_type = ctx.params.get("data", {}).get("config", {}).get("plot_type")
        if plot_type == 'histogram':
            print("histogram clicked")

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
        schemas = ctx.dataset.get_field_schema([fof.FloatField, fof.IntField], flat=True)
        for field_path in schemas.keys():
            fields.add_choice(field_path, label=field_path)
        return fields


    def create_axis_input(self, ctx, inputs, axis, is_heatmap):
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

        if not is_heatmap:
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
        autorange = ctx.params.get(f"{axis}axis", {}).get('autorange', True)
        # if not autorange:
            # axis_obj.array('range', element_type=types.Number(), default=None, label="Range", view=types.View(space=3))

        # todo - fix, this should not be a bool
        # axis_obj.bool('showexponent', default="all", label="Show Exponent")
        inputs.define_property(f"{axis}axis", axis_obj, label=f"{axis.capitalize()} Axis")

    def resolve_input(self, ctx):
        prompt = types.PromptView(submit_button_label="Create Plot")
        inputs = types.Object()
        inputs.str('plot_title', label='Plot Title', view=types.View(space=6))
        plot_choices = types.Choices(label="Plot Type", space=6)
        plot_choices.add_choice("histogram", label="Histogram")
        plot_choices.add_choice("line", label="Line")
        plot_choices.add_choice("scatter", label="Scatter")
        plot_choices.add_choice("eval_results", label="Evaluation Results")
        plot_choices.add_choice("heatmap", label="Heatmap")
        plot_choices.add_choice("bar", label="Bar")

        plot_type = ctx.params.get('plot_type')

        inputs.enum('plot_type', values=plot_choices.values(), view=plot_choices, required=True)
        is_heatmap = plot_type == 'heatmap' or plot_type == 'eval_results'

        if not plot_type:
            return types.Property(inputs, view=prompt)

        fields = self.get_number_field_choices(ctx)

        if plot_type == 'line' or plot_type == 'scatter':
            inputs.enum('y_field', values=fields.values(), view=fields, required=True, label="Y Data Source")
       
        if not is_heatmap:
            inputs.enum('x_field', values=fields.values(), view=fields, required=True, label="X Data Source")

        if plot_type == 'eval_results':
            eval_keys = types.Choices()
            for key in ctx.dataset.list_evaluations():
                eval_keys.add_choice(key, label=key)
            inputs.enum('eval_key', values=eval_keys.values(), view=eval_keys, required=True, label="Evaluation Key")

        self.create_axis_input(ctx, inputs, "x", is_heatmap)
        self.create_axis_input(ctx, inputs, "y", is_heatmap)


        if plot_type == 'histogram':
            inputs.int('bins', default=10, label="Number of Bins", view=types.View(space=6))
            inputs.obj('color', label="Color", default={"hex": '#ff0000'}, view=types.ColorView(compact=True))
            inputs.bool('show_legend', default=True, label="Show Legend")
            inputs.str('legend_title', default='Data', label="Legend Title")

            

            binning_function_choices = types.Choices()
            binning_function_choices.add_choice("count", label="Count")
            binning_function_choices.add_choice("sum", label="Sum")
            binning_function_choices.add_choice("avg", label="Average")
            binning_function_choices.add_choice("min", label="Minimum")
            binning_function_choices.add_choice("max", label="Maximum")
            inputs.enum('binning_function', values=binning_function_choices.values(), view=binning_function_choices, default="count", label="Binning Function")

            normalization_choices = types.Choices()
            normalization_choices.add_choice("", label="None")
            normalization_choices.add_choice("percent", label="Percent")
            normalization_choices.add_choice("probability", label="Probability")
            normalization_choices.add_choice("density", label="Density")
            normalization_choices.add_choice("probability density", label="Probability Density")
            inputs.enum('normalization', values=normalization_choices.values(), view=normalization_choices, default="", label="Normalization")

            inputs.bool('cumulative', default=False, label="Cumulative")

            histfunc_choices = types.Choices()
            histfunc_choices.add_choice("count", label="Count")
            histfunc_choices.add_choice("sum", label="Sum")
            histfunc_choices.add_choice("avg", label="Average")
            histfunc_choices.add_choice("min", label="Minimum")
            histfunc_choices.add_choice("max", label="Maximum")
            inputs.enum('histfunc', values=histfunc_choices.values(), view=histfunc_choices, default="count", label="Histogram Function")

        return types.Property(inputs, view=prompt)
    
    def execute(self, ctx):
        plot_config = ctx.params
        plot_config.pop('panel_state') # todo: remove this and panel_state from params
        return {"plot_config": plot_config}
        

def register(p):
    p.register(ConfigurePlot)
    p.register(CustomDashboard)
