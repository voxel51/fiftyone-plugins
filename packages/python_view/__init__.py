import fiftyone.operators as foo
import fiftyone.operators.types as types


class PythonView(foo.DynamicOperator):
  def __init__(self):
    super().__init__(
      "create_view_with_python",
      "Create View with Python",
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    inputs.str("python", label="Python", required=True)
    return types.Property(inputs)

  def execute(self, ctx):
    src = ctx.params.get("python", None)
    if src is None:
      return {}

    if not src.startswith("view."):
      return {"error": "Python must start with 'view.'"}
    
    view = eval(src, {"view": ctx.view})

    ctx.trigger("set_view", {"view": view._serialize()})

def register(p):
  p.register(PythonView)

