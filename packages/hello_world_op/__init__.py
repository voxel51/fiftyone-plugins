import fiftyone.operators as foo

class HelloWorldOperator(foo.Operator):
    def execute(self, ctx):
        return {
            "message": ctx.params.get("message") + " World!"
        }

operator = None

def register():
    operator = HelloWorldOperator(
        "hello-world",
        "Hello World Operator",
    )
    operator.definition.add_input_property("message", "string")
    operator.definition.add_output_property("message", "string")
    foo.register_operator(operator)

def unregister():
    foo.unregister_operator(operator)