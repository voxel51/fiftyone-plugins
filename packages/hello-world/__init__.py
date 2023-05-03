import fiftyone.operators as foo
import fiftyone.operators.types as types

class Count(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="count",
            label="Count"
        )
    
    def execute(self, ctx):
        return {"count": len(ctx.view)}

def register(p):
    p.register(Count)