import fiftyone.operators as foo
import fiftyone.operators.types as types


class PythonView(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="create_view_with_python",
      label="Create View with Python",
      dynamic=True,
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    src = ctx.params.get("python", None)
    py = inputs.str("python", label="Python", required=True)
    if src and not src.startswith("view."):
      inputs.str("error", label="Error", view=types.Error())
      py.invalid = True
      py.error_message = "Python must start with view."
    
    return types.Property(inputs)

  def execute(self, ctx):
    src = ctx.params.get("python", None)
    if src is None:
      return {}
    
    view = eval(src, {"view": ctx.dataset.view()})

    ctx.trigger("set_view", {"view": view._serialize()})

def register(p):
  p.register(PythonView)

