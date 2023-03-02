import fiftyone.operators as foo
import fiftyone.operators.types as types

class CountOperator(foo.Operator):
    def execute(self, ctx):
        return {
            "viewCount": ctx.view.count(),
            "count": ctx.dataset.count(),
            "selected": ctx.selected,
        }

op = None

def register():
    op = CountOperator("count", "Show number of samples in current dataset")
    op.definition.add_output_property("count", types.Number())
    op.definition.add_output_property("viewCount", types.Number())
    op.definition.add_output_property("selected", types.List(types.String()))
    foo.register_operator(op)

def unregister():
    foo.unregister_operator(op)

### NOTE: not trying to support session
### TODO: document all the python classes
### TODO: make it more obvious that an operator failed to load