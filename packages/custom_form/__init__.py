import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

class CustomFormOperator(foo.DynamicOperator):
    def resolve_input(self, ctx):
        inputs = types.Object()
        # an example message
        inputs.define_property(
            "heading",
            types.String(),
            view=types.Heading(
                label="Example Custom Form"
            )
        )
        inputs.define_property(
            "message",
            types.String(),
            view=types.Notice(
                label="Note",
                description="This is a custom Notice!",
                caption="this is a caption"
            )
        )

        if (ctx.params.get("my_operator_result", None)):
            inputs.define_property(
                "button",
                types.Trigger("my_operator",
                    params={
                        "foo", "bar"
                    },
                    target_param="my_operator_result"
                ),
                view=types.Button(
                    label="Click Me",
                    description="This is a custom Button!"
                )
            )
        else:
            inputs.define_property(
                "result",
                types.String(),
                view=types.Notice(
                    label="Note",
                    description="This is a custom Notice!",
                    caption="this is a caption"
                )
            )
        
        return types.Property(inputs)

    def my_callback(self, ctx):
        foo.execute_operator("my-airflow-status-operator", ctx)
        return {"message": "Hello World!"}

    def execute(self, ctx):
        return {}


class QueryBuilder(foo.DynamicOperator):
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.add_property(
            types.Property("field", types.Enum(ctx.dataset.get_field_schema().keys()))
        )
        field = ctx.params.get("field", None)
        if field:
            field_inst = ctx.dataset.get_field(field)
            if isinstance(field_inst, fo.EmbeddedDocumentField):
                field_schema = field_inst.get_field_schema()
                if (isinstance(field_schema.get('detections', None), fo.ListField)):
                    inputs.add_property(
                        types.Property("contains label", types.Enum(ctx.dataset.distinct(field + ".detections.label")))
                    )
            else:
                inputs.add_property(
                    types.Property("operation", types.Enum(["==", "!=", ">", "<", ">=", "<="]))
                )
                inputs.add_property(
                    types.Property("value", types.String())
                )

        return inputs
    def execute(self, ctx):
        return {}

op = None
qb = None
def register():
    op = CustomFormOperator(
        "dynamic_python_form",
        "Dynamic Python Form",
    )
    foo.register_operator(op)
    qb = QueryBuilder(
        "query_builder",
        "Search for Samples",
    )
    foo.register_operator(qb)

def unregister():
    foo.unregister_operator(op)
    foo.unregister_operator(qb)
