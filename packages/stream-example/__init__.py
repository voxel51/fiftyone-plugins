import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import asyncio

class StreamExample(foo.DynamicOperator):
    def __init__(self, plugin_definition=None):
        super().__init__(
            "stream-example",
            "Stream Example"
        )
        self.execute_as_generator = True

    async def execute(self, ctx):
        outputs = types.Object()
        outputs.str("message", label="Message", default="Hello World!")
        outputs.str("terminal", label="Terminal", view=types.CodeView(read_only=True, language="shell"))
        schema = types.Property(outputs)
        msg = ""
        for i in range(100):
            msg += "\n hello " + str(i)
            yield ctx.trigger(
                "show_output",
                {
                    "outputs": schema.to_json(),
                    "results": {
                        "message": "hello",
                        "terminal": msg
                    }
                }
            )
            await asyncio.sleep(1)
        # yield ctx.trigger("console_log", {"message": "Hello World!"})
        # for i in range(10):
        #     yield ctx.trigger("set_view", {"view": ctx.dataset.take(10, seed=i)._serialize()})
        #     await asyncio.sleep(1)

def register(p):
    p.register(StreamExample)