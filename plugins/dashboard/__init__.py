import fiftyone as fo
import fiftyone.operators as foo
from fiftyone.operators import types
import fiftyone.core.fields as fof
from fiftyone import ViewField as F


# class PlotPanelOperator(foo.Operator):
#     @property
#     def config(self):
#         return foo.OperatorConfig(
#             name="plot_panel_operator",
#             label="Plot Panel Operator",
#             description="Allows users to create various types of plots",
#             on_startup=True
#         )
    
#     def execute(self, ctx):
#         ctx.ops.register_panel(
#             name="plot_panel",
#             label="Dashboard",
#             on_load="@voxel51/dashboard/initialize_dashboard",
#             on_view_change="@voxel51/dashboard/plot_panel_view_change",
#             allow_duplicates=True
#         )

class Dashboard(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="dashboard",
            label="Dashboard",
            description="Dashboard for visualizing data",
            allow_multiple=True
        )
    
    def on_load(self, ctx):
        print('on load')
        # if ctx.panel.state.plot_config:
            # self.update_plot_data(ctx)

    def update_plot_data(self, ctx):
        print('update plot data --------')
        print(ctx.params)
        plot_config = ctx.panel.state.plot_config
        data = get_plot_data(ctx.dataset, plot_config)
        ctx.panel.data.plot = data

    def on_click_configure(self, ctx):
        ctx.prompt("@voxel51/dashboard/plotly_plot_operator", params=ctx.panel.state.plot_config, on_success=self.update_plot_data)

    def render(self, ctx):
        print('render')
        print(ctx.params)
        outputs = types.Object()
        menu = types.Object()
        outputs.define_property(
            "menu", menu, view=types.GridView(orientation="horizontal",align_x="center")
        )
        menu.btn("configure", label="Configure Dashboard", on_click=self.on_click_configure)
        if ctx.panel.state.plot_config:
            plot_config = ctx.panel.state.plot_config
            plot_view = get_plot_view(plot_config, self.on_plot_click)
            outputs.list("plot", types.Object(), view=plot_view)
        return types.Property(outputs, view=types.GridView(orientation="vertical", height=100, width=100))

    def on_plot_click(self, ctx):
        type = ctx.panel.state.plot_config.get('plot_type')
        # print('on plot click', ctx.params)
        if type == "histogram":
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
        elif type == "eval_results":
            print('heatmap x', ctx.params.get("x"))
            print('heatmap y', ctx.params.get("y"))
            set_view_for_confustion_matrix_cell(ctx, "ground_truth", "predictions", ctx.params.get("x"), ctx.params.get("y"))
        

def get_plot_data(sample_collection, plot_config):
    data = []
    plot_type = plot_config.get('plot_type')
    x_field = plot_config.get('x_field')
    is_line = plot_type == "line"
    is_scatter = plot_type == "scatter"
    if plot_type == "histogram":
        bins = plot_config.get('bins', 10)
        binning_function = plot_config.get('binning_function', 'count')
        normalization = plot_config.get('normalization', None)
        cumulative = plot_config.get('cumulative', False)
        histfunc = plot_config.get('histfunc', 'count')
        data = [{
            "type": "histogram",
            "x": sample_collection.values(x_field),
            "nbinsx": bins,
            "histfunc": histfunc,
            "cumulative_enabled": cumulative,
            # "marker": {"color": color},
            "xbin": {"func": binning_function},
            "histnorm": normalization,
        }]
    elif is_line or is_scatter:
        data = [{
            "type": "scatter",
            "mode": is_line and "lines" or "markers",
            "x": sample_collection.values(plot_config.get('x_field')),
            "y": sample_collection.values(plot_config.get('y_field'))
        }]
    elif plot_type == "heatmap":
        data =   [{
            "z": [[1, null, 30, 50, 1], [20, 1, 60, 80, 30], [30, 60, 1, -10, 20]],
            "x": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            "y": ['Morning', 'Afternoon', 'Evening'],
            "type": 'heatmap',
            "hoverongaps": False
        }]
    elif plot_type == "bar":
        data = [{"type": "bar", "x": [1, 2, 3], "y": [1, 4, 9]}]
    elif plot_type == "eval_results":
        eval_key = plot_config.get('eval_key')
        eval_results = sample_collection.load_evaluation_results(eval_key)
        confusion_matrix = eval_results.confusion_matrix().tolist()
        labels = list(eval_results.classes)

        print('labels length', len(labels))
        print('confusion matrix length', len(confusion_matrix))

        data = [{
            "type": "heatmap",
            "z": confusion_matrix,
            "x": labels,
            "y": labels
        }]

    return data


def set_view_for_confustion_matrix_cell(ctx, x_field, y_field, x, y):
    view = ctx.dataset.filter_labels(x_field, F("label") == x)
    view = view.filter_labels(y_field, F("label") == y)
    ctx.ops.set_view(view)

def get_axis_config(plot_config, axis):
        axis_config = plot_config.get(f"{axis}axis", None)    
        return axis_config

def get_plot_view(plot_config, on_click=None):
    panel_id = plot_config.get('panel_id') # this should come from ctx (not params)
    plot_type = plot_config.get('plot_type')
    plot_title = plot_config.get('plot_title', None)
    config = {}
    show_legend = plot_config.get('show_legend', False)
    layout = {
        "title": plot_title,
        "xaxis": get_axis_config(plot_config, "x"),
        "yaxis": get_axis_config(plot_config, "y"),
        "showlegend": show_legend,
    }
    x_field = plot_config.get('x_field')
    y_field = plot_config.get('y_field')
    # is_line = plot_type == "line"
    # is_scatter = plot_type == "scatter"
    # is_eval_results = plot_type == "eval_results"

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
        on_click=on_click,
        x_data_source=plot_config.get('x_field'),
        show_selected=True,
        height=85
    )

    return plotly_view

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

        self.create_axis_input(ctx, inputs, "x", is_heatmap)
        self.create_axis_input(ctx, inputs, "y", is_heatmap)

        fields = self.get_number_field_choices(ctx)
        if not is_heatmap:
            inputs.enum('x_field', values=fields.values(), view=fields, required=True, label="X Data Source")

        if plot_type == 'eval_results':
            eval_keys = types.Choices()
            for key in ctx.dataset.list_evaluations():
                eval_keys.add_choice(key, label=key)
            inputs.enum('eval_key', values=eval_keys.values(), view=eval_keys, required=True, label="Evaluation Key")

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

        return types.Property(inputs, view=prompt)
    
    def execute(self, ctx):
        plot_config = ctx.params
        plot_config.pop('panel_state') # todo: remove this and panel_state from params

        # NOTE: this should not be needed
        #       so that operators can be composed
        #       without needing to know about
        #       each other
        ctx.panel.state.plot_config = plot_config
        return {"plot_config": plot_config}
        
def register(plugin):
    plugin.register(Dashboard)
    plugin.register(PlotlyPlotOperator)
