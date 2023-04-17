import fiftyone.operators as foo
import fiftyone.operators.types as types

class ClearDataset(foo.DynamicOperator):
    def __init__(self):
        super().__init__("clear_dataset", "Clear dataset")
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.define_property("dataset_name", types.String(),
            label="Dataset Name",
            description="Type the dataset name to verify that you want to clear it")
        return types.Property(inputs)

    def execute(self, ctx):
        dataset_name = ctx.params.get("dataset_name", None)
        print(dataset_name)
        print(ctx.dataset_name)
        if dataset_name == ctx.dataset_name:
            ctx.dataset.clear()
            ctx.trigger("reload_samples")
        else:
            return {
                "dataset_cleared": False,
                "error": "Dataset name does not match"
            }
        return {
            "dataset_cleared": True
        }
        
op = None

def register():
    op = ClearDataset()
    foo.register_operator(op)
def unregister():
    foo.unregister_operator(op)
