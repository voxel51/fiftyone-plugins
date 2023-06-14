import fiftyone.operators as foo
import fiftyone.operators.types as types
from time import sleep


class Count(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="count", label="Count")

    def execute(self, ctx):
        return {"count": len(ctx.view)}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.int("count")
        return types.Property(outputs)


def register(p):
    p.register(Count)
