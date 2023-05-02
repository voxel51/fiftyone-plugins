import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import asyncio


class ProgressExample(foo.Operator):
    def __init__(self):
        super().__init__("progress-example", "Progress Example")
        self.execute_as_generator = True

    async def execute(self, ctx):
        outputs = types.Object()
        schema = types.Property(outputs)
        MAX = 100
        for i in range(MAX):
            progress_label = f"Loading {i} of {MAX}"
            progress_view = types.ProgressView(label=progress_label)
            loading_schema = types.Object()
            loading_schema.int("percent_complete", view=progress_view)
            show_output_params = {
                "outputs": types.Property(loading_schema).to_json(),
                "results": {"percent_complete": i / MAX}
            }
            yield ctx.trigger("show_output", show_output_params)
            # simulate computation
            await asyncio.sleep(0.5)

def register(p):
    p.register(ProgressExample)