import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

class Trigger(foo.Operator):
    def __init__(self):
        super().__init__(
            "trigger_example",
            "Example Trigger Operator"
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.define_property(
            "operator_to_trigger",
            types.Enum([
                "clear_view",
                "set_view",
                "reload_samples",
                "open_panel"
            ]),
            label="Operator to trigger"
        )
        return types.Property(inputs)

    def execute(self, ctx):
        operator_to_trigger = ctx.params.get("operator_to_trigger", None)
        params = {}
        if (operator_to_trigger == "set_view"):
            view_to_set = ctx.dataset.limit(3)._serialize()
            params = {"view": view_to_set}

        if (operator_to_trigger == "open_panel"):
            params = {
                "name": "Embeddings",
                "isActive": True,
            }

        ctx.trigger(operator_to_trigger, params=params)

class ShowRandomSamples(foo.Operator):
    def __init__(self):
        super().__init__(
            "show_random_samples",
            "Show Random Samples"
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.define_property(
            "number_of_samples",
            types.Number(),
            label="Number of samples to show",
            default=10
        )
        return types.Property(inputs)
        
    def execute(self, ctx):
        number_of_samples = ctx.params.get("number_of_samples", None)
        samples = ctx.dataset.take(number_of_samples).values('id')
        ctx.trigger("show_samples", params={"samples": samples})

#
# How do triggers work?
#
# Flow of an operator:
# 1. The operator is registered with the foo.register_operator() function
# 2. A request to execute the operator is made by the user (or another operator)
# 3. The operator is executed by the foo.execute_operator() function
# 4. The operator's execute() function is called, which may call "trigger" to execute other operators
# 5. The result of the operator is returned to the user, or if the operator fails to execute the error is returned
# 6. Unless an error occured, any triggered operators are executed by following this same flow until
# 7. Steps 2-6 are repeated until no more operators register a trigger
#
# NOTE: step 6 is done on the client triggering the operator (which may be python or javascript)
# 
#
# Why use triggers?
#
# 1. To change state in the application as the result of exeuctiong a python operator
# 2. To re-use existing behavior such as loading a new dataset once it has been imported
# 3. To allow for the execution of multiple operators as one or independently:
#    - eg. a set of operators that allow remapping fields:
#      - change field name
#      - change field type
#      - remap field values
#      - These could be combined into a single operator that does all of these things
#      - Or a single operator that allows for one of these for multipl fields.
#
# Note: if paramaters are provided when executing an operator directly or via trigger, then
# that operator will not prompt the user for input. If no parameters are provided, then the
# operator will prompt the user for input (if inputs are defined).


def register(p):
    p.register(Trigger)
    p.register(ShowRandomSamples)

