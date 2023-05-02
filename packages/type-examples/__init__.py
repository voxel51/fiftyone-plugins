import fiftyone.operators as foo
import fiftyone.operators.types as types

class TypeExamples(foo.Operator):
  def __init__(self):
    super().__init__(
      "type_examples",
      "Type Examples",
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    available_types = [
      types.Object,
      types.TableView,
      types.PlotlyView
    ]
    all_choices = [types.Choice(t.__name__, label=t.__name__) for t in available_types]
    choices = types.Dropdown(choices=all_choices)
    inputs.enum("type", choices.values(), label="Type", required=True, view=choices)
    return types.Property(inputs)

  def execute(self, ctx):
    view_type = ctx.params.get("type", None)
    if view_type == "TableView":
      return {"table": [
        {
          "type": "Tumor (Positive)",
          "dt_tumor": 38,
          "dt_non_tumor": 2,
          "reg_tumor": 40,
          "reg_non_tumor": 22,
        },
        {
          "type": "Non-Tumor (Negative)",
          "dt_tumor": 19,
          "dt_non_tumor": 439,
          "reg_tumor": 5,
          "reg_non_tumor": 42,
        }
      ]}
    elif view_type == "PlotlyView":
      return {"plot": [
        {
          "x": [1, 2, 3],
          "y": [2, 6, 3],
          "type": 'scatter',
          "mode": 'lines+markers',
          "marker": {"color": 'red'},
        }
      ]}

  def resolve_output(self, ctx):
    view_type = ctx.params.get("type", None)
    outputs = types.Object()
    table = types.TableView()
    table.add_column("type", label="")
    table.add_column("dt_tumor", label="Tumor (Decision Tree)")
    table.add_column("dt_non_tumor", label="Non Tumor (Decision Tree)")
    table.add_column("reg_tumor", label="Tumor (Regression)")
    table.add_column("reg_non_tumor", label="Non Tumor (Regression)")
    outputs.list("table", types.Object(), label="Table", view=table)
    plotly = types.PlotlyView(label="My Plotly", data=[
      {
        "x": [1, 2, 3],
        "y": [2, 6, 3],
        "type": 'scatter',
        "mode": 'lines+markers',
        "marker": {"color": 'red'}
      }
    ])
    outputs.list("plot", types.Object(), view=plotly)
    return types.Property(outputs)

def register(p):
  p.register(TypeExamples)


