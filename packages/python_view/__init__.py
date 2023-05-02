import fiftyone.operators as foo
import fiftyone.operators.types as types


class PythonView(foo.Operator):
  def __init__(self):
    super().__init__(
      "create_view_with_python",
      "Create View with Python",
    )
    self.is_dynamic = True
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    src = ctx.params.get("python", None)
    py = inputs.str("python", label="Python", required=True)
    if src and (not src.startswith("view.") and not src.startswith("dataset.")):
      inputs.str("error", label="Error", view=types.Error())
      py.invalid = True
      py.error_message = "Python must start with view. or dataset."
    
    return types.Property(inputs)

  def execute(self, ctx):
    src = ctx.params.get("python", None)
    if src is None:
      return {}
    
    view = eval(src, {"view": ctx.view, "dataset": ctx.dataset})

    ctx.trigger("set_view", {"view": view._serialize()})

def register(p):
  p.register(PythonView)

