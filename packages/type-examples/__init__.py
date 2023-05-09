import fiftyone.operators as foo
import fiftyone.operators.types as types

###
### Advanced Input
###

class ChoicesExample(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="example_choices",
      label="Examples: Choices",
    )

  def resolve_input(self, ctx):
    inputs = types.Object()
    radio_choices = types.RadioGroup()
    radio_choices.add_choice("choice1", label="Choice 1")
    radio_choices.add_choice("choice2", label="Choice 2")
    radio_choices.add_choice("choice3", label="Choice 3")
    inputs.enum("radio_choices", radio_choices.values(), default=radio_choices.choices[0].value, label="Radio Choices", view=radio_choices)
    dropdown_choices = types.Dropdown()
    dropdown_choices.add_choice("choice1", label="Choice 1")
    dropdown_choices.add_choice("choice2", label="Choice 2")
    dropdown_choices.add_choice("choice3", label="Choice 3")
    inputs.enum("dropdown_choices", dropdown_choices.values(), default=dropdown_choices.choices[0].value, label="Radio Choices", view=dropdown_choices)
    return types.Property(inputs)

  def execute(self, ctx):
    return {"radio_choice": ctx.params["radio_choices"], "dropdown_choice": ctx.params["dropdown_choices"]}

  def resolve_output(self, ctx):
    outputs = types.Object()
    outputs.str("radio_choice", label="Radio Choice")
    outputs.str("dropdown_choice", label="Dropdown Choice")
    return types.Property(outputs)

class InputListExample(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="example_input_list",
      label="Examples: Input List",
    )

  def resolve_input(self, ctx):
    default_people = [
      {"first_name": "Terry", "last_name": "Doe"},
      {"first_name": "Florence", "last_name": "Doe"},
      {"first_name": "Bill", "last_name": "Smith"},
      {"first_name": "Haley", "last_name": "Smith"},
      {"first_name": "Tim", "last_name": "Jones"},
      {"first_name": "Jordan", "last_name": "Jones"},
    ]

    inputs = types.Object()
    list_row = types.Object()
    # space is the number of columns to span out of 12
    list_row_cell = types.View(space=6)
    list_row.str("first_name", label="First Name", view=list_row_cell)
    list_row.str("last_name", label="Last Name", view=list_row_cell)
    inputs.list("list", list_row, label="List", default=default_people)
    return types.Property(inputs)

  def execute(self, ctx):
    return {"people": [person.get("first_name") for person in ctx.params["list"]]}
  
  def resolve_output(self, ctx):
    outputs = types.Object()
    outputs.list("people", types.String(), label="People")
    return types.Property(outputs)

###
### Advanced Output
###

class ImageExample(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="example_image",
      label="Examples: Image",
    )
  
  def execute(self, ctx):
    samples = ctx.dataset.limit(10)
    img_urls = [f"http://localhost:5151/media?filepath={sample.filepath}" for sample in samples]
    return {"images": img_urls}
  
  def resolve_output(self, ctx):
    outputs = types.Object()
    outputs.define_property(
      "images",
      types.List(types.String()),
      label="Images",
      view=types.ListView(items=types.ImageView())
    )
    return types.Property(outputs)

class TableExample(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="example_table",
      label="Examples: Table",
    )
  def execute(self, ctx):
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

  def resolve_output(self, ctx):
    outputs = types.Object()
    table = types.TableView()
    table.add_column("type", label="")
    table.add_column("dt_tumor", label="Tumor (Decision Tree)")
    table.add_column("dt_non_tumor", label="Non Tumor (Decision Tree)")
    table.add_column("reg_tumor", label="Tumor (Regression)")
    table.add_column("reg_non_tumor", label="Non Tumor (Regression)")
    outputs.list("table", types.Object(), label="Table", view=table)
    return types.Property(outputs)

class PlotExample(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="example_plot",
      label="Examples: Plot",
    )
  
  def execute(self, ctx):
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
    outputs = types.Object()
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
  p.register(PlotExample)
  p.register(TableExample)
  p.register(InputListExample)
  p.register(ChoicesExample)
  p.register(ImageExample)


