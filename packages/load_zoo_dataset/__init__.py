import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo
import fiftyone.zoo as foz

class LoadZooDatasetOperator(foo.Operator):
    def execute(self, ctx):
        dataset_name = ctx.params.get('fiftyone_dataset_name')
        dataset = foz.load_zoo_dataset(dataset_name)
        return {
            "result": {
                "dataset_name": dataset_name
            }
        }

def register():
    operator = LoadZooDatasetOperator(
        "load-zoo-dataset",
        "Load Zoo Dataset",
    )
    zoo_datasets = foz.list_zoo_datasets()
    operator.inputs.define_property("fiftyone_dataset_name", types.Enum(zoo_datasets))
    foo.register_operator(operator)

def unregister():
    foo.unregister_operator(operator)
