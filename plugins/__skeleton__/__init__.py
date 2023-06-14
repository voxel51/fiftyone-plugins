import fiftyone.operators as foo
import fiftyone.operators.types as types


class Greet(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="{{PLUGIN_NAME}}_greet_py",
            label="{{PLUGIN_NAME}}: Greet from Py"
        )

    def execute(self, ctx):
        return {"greeting": "Hi " + ctx.params["name"]}

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("name")
        return types.Property(inputs)

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("greeting")
        return types.Property(outputs)

    # Uncomment class method below to add a placement for this operator
    # def resolve_placement(self, ctx):
    #     return types.Placement(
    #         # Display placement in the actions row of samples grid
    #         types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
    #         # Display a button as the placement
    #         types.Button(
    #             # label for placement button visible on hover
    #             label="{{PLUGIN_NAME}}: Greet",
    #             # icon for placement button. If not provided, button with label
    #             # will be displayed
    #             icon="/assets/greet.svg",
    #             # skip operator prompt when we do not require an input from
    #             # the user by setting prompt to False
    #             prompt=True
    #         )
    #     )


def register(p):
    p.register(Greet)
