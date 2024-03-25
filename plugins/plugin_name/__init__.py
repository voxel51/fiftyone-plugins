import fiftyone as fo
import fiftyone.operators as foo
from fiftyone.operators import types


class TestPlotOperator(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="test_plot_operator",
            label="My Plot Operator",
            description="My operator description",
            dynamic=True
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str('panel_id') # this should be automatically added by inheriting from foo.PanelOperator or similar
        choices = types.Choices()
        choices.add_choice("Viridis", label="Viridis")
        choices.add_choice("Plasma", label="Plasma")
        inputs.enum('colorscale', values=choices.values(), view=choices)
        return types.Property(inputs)
    
    def execute(self, ctx):
        outputs = types.Object()
        plotly = types.PlotlyView(label="My Plotly")
        outputs.list("plot", types.Object(), view=plotly)
        ctx.trigger("set_panel_params", {
            "panel_id": ctx.params['panel_id'],
            "params": ctx.params
        })
        ctx.trigger("show_panel_output", {
            "panel_id": ctx.params['panel_id'],
            "outputs": types.Property(outputs).to_json(),
            "data": {
                "plot": [
                    {
                        "colorscale": ctx.params.get("colorscale", "Viridis"),
                        "z": [
                            [1, 20, 30, 50, 1],
                            [20, 1, 60, 80, 30],
                            [30, 60, 1, -10, 20]
                        ],
                        "type": "heatmap",
                        "hoverongaps": False
                    }
                ]
            }
        })

import fiftyone.core.fields as fof

class PlotlyPlotOperator(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="plotly_plot_operator",
            label="Plotly Plot Operator",
            description="Allows users to create various types of Plotly plots",
            dynamic=True
        )
    
    def get_number_field_choices(self, ctx):
        fields = types.Choices(space=6)
        schemas = ctx.dataset.get_field_schema([fof.FloatField, fof.IntField], flat=True)
        for field_path in schemas.keys():
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
        scale_choices.add_choice("category", label="Date")
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
        inputs = types.Object()

        inputs.str('plot_title', label='Plot Title', view=types.View(space=6))
        plot_choices = types.Choices(label="Plot Type", space=6)
        plot_choices.add_choice("histogram", label="Histogram")
        plot_choices.add_choice("line", label="Line")
        plot_choices.add_choice("scatter", label="Scatter")
        plot_choices.add_choice("heatmap", label="Heatmap")
        plot_choices.add_choice("bar", label="Bar")

        plot_type = ctx.params.get('plot_type')

        inputs.enum('plot_type', values=plot_choices.values(), view=plot_choices, required=True)

        self.create_axis_input(ctx, inputs, "x")
        self.create_axis_input(ctx, inputs, "y")

        fields = self.get_number_field_choices(ctx)
        inputs.enum('x_field', values=fields.values(), view=fields, required=True, label="X Data Source")

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

        if plot_type == 'line' or plot_type == 'scatter':
            inputs.enum('y_field', values=fields.values(), view=fields, required=True, label="Y Data Source")

        prompt = types.PromptView(submit_button_label="Create Plot")
        return types.Property(inputs, view=prompt)
    
    def get_axis_config(self, ctx, axis, plot_type):
        return ctx.params.get(f"{axis}axis", None)    

    def execute(self, ctx):
        panel_id = ctx.params.get('panel_id') # this should come from ctx (not params)
        plot_type = ctx.params.get('plot_type')
        plot_title = ctx.params.get('plot_title', None)
        data = []
        config = {}
        show_legend = ctx.params.get('show_legend', False)
        layout = {
            "title": plot_title,
            "xaxis": self.get_axis_config(ctx, "x", plot_type),
            "yaxis": self.get_axis_config(ctx, "y", plot_type),
            "showlegend": show_legend,
        }
        x_field = ctx.params.get('x_field')
        y_field = ctx.params.get('y_field')
        is_line = plot_type == "line"
        is_scatter = plot_type == "scatter"

        # Based on the plot type, we would populate 'data', 'config', and 'layout' appropriately
        if plot_type == "histogram":
            bins = ctx.params.get('bins', 10)
            binning_function = ctx.params.get('binning_function', 'count')
            normalization = ctx.params.get('normalization', None)
            cumulative = ctx.params.get('cumulative', False)
            histfunc = ctx.params.get('histfunc', 'count')
            color = ctx.params.get('color', {"hex": '#1f77b4'})['hex']

            legend_title = ctx.params.get('legend_title', 'Data')

            data = [{
                "type": "histogram",
                "x": ctx.view.values(x_field),
                "nbinsx": bins,
                "histfunc": histfunc,
                "cumulative_enabled": cumulative,
                # "marker": {"color": color},
                "xbin": {"func": binning_function}
            }]

            if normalization:
                data[0]['histnorm'] = normalization

            config = {}
        elif is_line or is_scatter:
            data = [{
                "type": "scatter",
                "mode": is_line and "lines" or "markers",
                "x": ctx.view.values(ctx.params.get('x_field')),
                "y": ctx.view.values(ctx.params.get('y_field'))
            }]
        elif plot_type == "heatmap":
            data = [{"type": "heatmap", "z": [[1, 20, 30], [20, 1, 60], [30, 60, 1]]}]
        elif plot_type == "bar":
            data = [{"type": "bar", "x": [1, 2, 3], "y": [1, 4, 9]}]

        actual_title = plot_title
        if not plot_title:
            if x_field:
                actual_title = f"{plot_title} ({x_field})"
            if y_field:
                actual_title = f"{plot_title} ({x_field}, {y_field})"

        # Construct the Plotly view (note: panel_id should be auto injected somehow)
        plotly_view = types.PlotlyView(
            panel_id=panel_id,
            label=actual_title,
            config=config,
            layout=layout,
            controller="@github_username/plugin_name/plotly_plot_controller",
            x_data_source=ctx.params.get('x_field'),
            show_selected=True
        )

        outputs = types.Object()
        outputs.list("plot", types.Object(), view=plotly_view)

        ctx.trigger("show_panel_output", {
            "panel_id": panel_id,
            "outputs": types.Property(outputs).to_json(),
            "data": {
                "plot": data,  # Pass the data to the Plotly plot
            }
        })

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Plot generated")
        return types.Property(outputs, view=view)


class PlotlyPlotController(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="plotly_plot_controller",
            label="Plotly Plot Controller",
            dynamic=True,
            unlisted=True
        )

    def execute(self, ctx):
        event = ctx.params.get('event')
        print(ctx.params)
        if event == 'onClick':
            min = ctx.params.get("range", [])[0]
            max = ctx.params.get("range", [])[1]
            filter = {}
            filter[ctx.params.get("x_data_source")] = {"$gte": min, "$lte": max}
            ctx.trigger("set_view", dict(view=[
                {
                    "_cls": "fiftyone.core.stages.Match",
                    "kwargs": [
                    [
                        "filter",
                        filter
                    ]
                    ],
                }
            ]))



def register(plugin):
    plugin.register(TestPlotOperator)
    plugin.register(PlotlyPlotOperator)
    plugin.register(PlotlyPlotController)
