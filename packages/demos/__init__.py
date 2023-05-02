import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

class SelectRandomSamples(foo.Operator):
  def __init__(self):
    super().__init__(
      "select_random_samples",
      "Select Random Samples",
    )
    self.is_dynamic = True

  def resolve_input(self, ctx):
    inputs = types.Object()
    inputs.int(
      "number_of_samples",
      label="Number of samples",
      required=True,
      default=10,
      description="Number of samples to select",
    )
    return types.Property(inputs)

  def execute(self, ctx):
    random_samples = ctx.dataset.take(ctx.params["number_of_samples"])
    ids = [sample.id for sample in random_samples]
    ctx.trigger("set_selected_samples", {"samples": ids})
    ctx.trigger("show_samples", {"samples": ids})


class HelloWorld(foo.Operator):
  def __init__(self):
    super().__init__(
      "hello_world",
      "Hello World",
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    inputs.str(
      "name",
      label="Message",
      required=True,
      default="Hello",
      description="Message to greet",
    )
    return types.Property(inputs)

  def execute(self, ctx):
    return {
      "message": "%s, World!" % ctx.params["name"]
    }

  def resolve_output(self, ctx):
    outputs = types.Object()
    return types.Property(outputs, view=types.InferredView())

def register(p):
  p.register(SelectRandomSamples)
  p.register(HelloWorld)