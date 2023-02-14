import fiftyone.operators as foo
import fiftyone as fo
import fiftyone.brain as fob

class HelloWorldOperator(foo.Operator):
    def execute(self, ctx):
        return {
            "message": ctx.params.get("message") + " World!"
        }

class CountOperator(foo.Operator):
    def execute(self, ctx):
        # view = ctx.view - this is not working due to odd migration error
        view = fo.load_dataset('mnist')
        return {
            "count": view.count()
        }

class ComputeSimilarityOperator(foo.Operator):
    def execute(self, ctx):
        # view = ctx.view - this is not working due to odd migration error
        view = ctx.view
        brain_key = ctx.params.get("brain_key")
        model_name = ctx.params.get("model_name", None)
        result = fob.compute_similarity(view, brain_key=brain_key, model=model_name)
        return {
            "config": result.config
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

    sim_operator = ComputeSimilarityOperator('compute-similarity', 'Compute Similarity')
    sim_operator.definition.add_input_property('brain_key', 'string')
    sim_operator.definition.add_input_property('model_name', 'string')
    sim_operator.definition.add_output_property('config', 'object')
    foo.register_operator(sim_operator)


    count_operator = CountOperator('count', 'Count Items in the Current View')
    count_operator.definition.add_output_property('count', 'string')
    foo.register_operator(count_operator)

def unregister():
    foo.unregister_operator(operator)