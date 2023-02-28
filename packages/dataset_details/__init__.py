import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo
import fiftyone.zoo as foz

class DetailOperator(foo.Operator):
    def execute(self, ctx):
        view = ctx.view
        # name = ctx.dataset_name
        dataset_name = ctx.params.get("dataset_name")
        dataset = fo.load_dataset(dataset_name)
        count = view.count()
        return {
            "name": name,
            "count": count
        }

class CountOperator(foo.Operator):
    def execute(self, ctx):
        view = ctx.view
        count = view.count()
        return {
            "count": count
        }


class LoadFromZooOperator(foo.Operator):
    def execute(self, ctx):
        dataset_name = ctx.params.get("dataset_name")
        dataset = foz.load_zoo_dataset(dataset_name)
        dataset.persistent = True


op = None
c = None
z = None

def register():
    z = LoadFromZooOperator("load-from-zoo", "Loads a dataset from the FiftyOne Zoo")
    z.definition.add_input_property("dataset_name", types.Enum(foz.list_zoo_datasets()))
    foo.register_operator(z)

    op = DetailOperator("get-details", "Gets the details of a dataset")
    op.definition.add_input_property("dataset_name", types.String())
    p = op.definition.add_output_property("name", types.String())
    p.description = "The name of the dataset"
    op.definition.add_output_property("count", types.Number())
    foo.register_operator(op)

    c = CountOperator("count", "Counts the number of samples in a dataset")
    c.definition.add_output_property("count", types.Number())
    foo.register_operator(c)


def unregister():
    foo.unregister_operator(op)
    foo.unregister_operator(c)