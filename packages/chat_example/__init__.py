# a fiftyone operator that accepts a query as a string
# and returns the results as an array of strings

import fiftyone.operators as foo
import fiftyone.operators.types as types


class SearchDatasetWithGPTP4anel(foo.Operator):
    def __init__(self):
        super().__init__("search-dataset-with-gpt4", "Search Dataset with GPT4")

    def resolve_placement(self, ctx):
        return types.Placement(types.Places.SAMPLES_GRID_ACTIONS, view=types.Button(label="Search with GPT4", icon_url="/plugins/chat_example/openai-icon.svg"))

    def execute(self, ctx):
        ctx.trigger("open_panel", {"panel": "gpt4"})

op = None

def register():
    op = SearchDatasetWithGPTP4anel()
    foo.register_operator(op)

def unregister():
    foo.unregister_operator(op)