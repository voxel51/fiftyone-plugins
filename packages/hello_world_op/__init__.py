import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

class HelloWorld(foo.DynamicOperator):
    def __init__(self, plugin_definition=None):
        super().__init__(
            "hello_world_op",
            "Hello World"
        )
        
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.define_property("message", types.String(), label="Message")            
        return types.Property(inputs)

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.define_property("message", types.String(), label="Message")            
        return types.Property(outputs)

    def execute(self, ctx):
        return {
            "message": ctx.params.get("message") + " World!"
        }

def register(p):
    p.register(HelloWorld)