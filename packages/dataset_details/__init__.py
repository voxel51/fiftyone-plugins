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
    op.define_output_property("count", types.Number())
    op.define_output_property("viewCount", types.Number())
    foo.register_operator(op)

def unregister():
    foo.unregister_operator(op)
