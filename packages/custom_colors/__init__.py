import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

class CustomColors(foo.DynamicOperator):
    def __init__(self):
        super().__init__(
            name="Custom Colors",
            description="Customize Field Colors"
        )
    def resolve_input(self, ctx):
        inputs = types.Object()
        field = ctx.params.get("field", None)
        if field is not None:
            # TODO - change this to a header
            inputs.define_property("header", types.String(), label="Header", defautl=field)
            # TODO - change to a types.ColorView()
            inputs.str("color", required=True, view=types.Color(label="Color", description="Choose a color for this field"))

            inputs.bool("something", label="Something", default=False)
        else:
            inputs.enum("field", ctx.dataset.get_field_schema().keys(), required=True)
        return types.Property(inputs)
    def execute(self, ctx):
        return {}

op = None
def register():
    pass
    # op = CustomColors()
    # foo.register_operator(op)
def unregister():
    pass
    # foo.unregister_operator(op)
