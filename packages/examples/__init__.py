import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo
import asyncio

###
### Simple Input
###
class SimpleInputExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_simple_input",
            label="Examples: Simple Input",
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("message", label="Message", required=True)
        return types.Property(inputs)

    def execute(self, ctx):
        return {"message": ctx.params["message"]}
    
    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("message", label="Message")
        return types.Property(outputs)

###
### Advanced Input
###


class ChoicesExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_choices",
            label="Examples: Choices",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        radio_choices = types.RadioGroup()
        radio_choices.add_choice("choice1", label="Choice 1")
        radio_choices.add_choice("choice2", label="Choice 2")
        radio_choices.add_choice("choice3", label="Choice 3")
        inputs.enum(
            "radio_choices",
            radio_choices.values(),
            default=radio_choices.choices[0].value,
            label="Radio Choices",
            view=radio_choices,
        )
        dropdown_choices = types.Dropdown()
        dropdown_choices.add_choice("choice1", label="Choice 1")
        dropdown_choices.add_choice("choice2", label="Choice 2")
        dropdown_choices.add_choice("choice3", label="Choice 3")
        inputs.enum(
            "dropdown_choices",
            dropdown_choices.values(),
            default=dropdown_choices.choices[0].value,
            label="Radio Choices",
            view=dropdown_choices,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        return {
            "radio_choice": ctx.params["radio_choices"],
            "dropdown_choice": ctx.params["dropdown_choices"],
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("radio_choice", label="Radio Choice")
        outputs.str("dropdown_choice", label="Dropdown Choice")
        return types.Property(outputs)


class InputListExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_input_list",
            label="Examples: Input List",
        )

    def resolve_input(self, ctx):
        default_people = [
            {"first_name": "Terry", "last_name": "Doe"},
            {"first_name": "Florence", "last_name": "Doe"},
            {"first_name": "Bill", "last_name": "Smith"},
            {"first_name": "Haley", "last_name": "Smith"},
            {"first_name": "Tim", "last_name": "Jones"},
            {"first_name": "Jordan", "last_name": "Jones"},
        ]

        inputs = types.Object()
        list_row = types.Object()
        # space is the number of columns to span out of 12
        list_row_cell = types.View(space=6)
        list_row.str("first_name", label="First Name", view=list_row_cell)
        list_row.str("last_name", label="Last Name", view=list_row_cell)
        inputs.list("list", list_row, label="List", default=default_people)
        return types.Property(inputs)

    def execute(self, ctx):
        return {"people": [person.get("first_name") for person in ctx.params["list"]]}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.list("people", types.String(), label="People")
        return types.Property(outputs)


###
### Advanced Output
###


class ImageExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_image",
            label="Examples: Image",
        )

    def execute(self, ctx):
        samples = ctx.dataset.limit(10)
        img_urls = [
            f"http://localhost:5151/media?filepath={sample.filepath}"
            for sample in samples
        ]
        return {"images": img_urls}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.define_property(
            "images",
            types.List(types.String()),
            label="Images",
            view=types.ListView(items=types.ImageView()),
        )
        return types.Property(outputs)


class TableExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_table",
            label="Examples: Table",
        )

    def execute(self, ctx):
        return {
            "table": [
                {
                    "type": "Tumor (Positive)",
                    "dt_tumor": 38,
                    "dt_non_tumor": 2,
                    "reg_tumor": 40,
                    "reg_non_tumor": 22,
                },
                {
                    "type": "Non-Tumor (Negative)",
                    "dt_tumor": 19,
                    "dt_non_tumor": 439,
                    "reg_tumor": 5,
                    "reg_non_tumor": 42,
                },
            ]
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        table = types.TableView()
        table.add_column("type", label="")
        table.add_column("dt_tumor", label="Tumor (Decision Tree)")
        table.add_column("dt_non_tumor", label="Non Tumor (Decision Tree)")
        table.add_column("reg_tumor", label="Tumor (Regression)")
        table.add_column("reg_non_tumor", label="Non Tumor (Regression)")
        outputs.list("table", types.Object(), label="Table", view=table)
        return types.Property(outputs)


class PlotExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_plot",
            label="Examples: Plot",
        )

    def execute(self, ctx):
        return {
            "plot": [
                {
                    "z": [
                        [1, None, 30, 50, 1],
                        [20, 1, 60, 80, 30],
                        [30, 60, 1, -10, 20],
                    ],
                    "x": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "y": ["Morning", "Afternoon", "Evening"],
                    "type": "heatmap",
                    "hoverongaps": False,
                }
            ]
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        plotly = types.PlotlyView(label="My Plotly")
        outputs.list("plot", types.Object(), view=plotly)
        return types.Property(outputs)

class ExampleSlideshow(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_slideshow",
            label="Examples: Slideshow",
            dynamic=True,
            execute_as_generator=True,
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()
        msg = inputs.str("msg", view=types.Warning(label="This operator is intended to be used with the quickstart-video dataset."))
        if ctx.dataset_name != "quickstart-video":
            msg.invalid = True
        return types.Property(inputs)
    
    async def execute(self, ctx):
        group = ctx.view.first()
        
        fo.pprint(group)
        fo.pprint(group.frames[1])

        outputs = types.Object()
        outputs.str("frame_url", view=types.ImageView(space=12, image={"width": "80%"}))
        outputs.int("progress", view=types.ProgressView())
        frame_count = len(group.frames)
        for frame_number in range(1, frame_count):
            frame = group.frames[frame_number]
            await asyncio.sleep(0.04)
            yield ctx.trigger(
                "show_output",
                {
                    "outputs": types.Property(outputs).to_json(),
                    "results": {
                        "frame_url": f"http://localhost:5151/media?filepath={frame.filepath}",
                        "progress": frame_number / (frame_count - 1),
                    }
                }
            )

###
### Show Output
###


class ExampleShowOutput(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_output_styles",
            label="Examples: Output Styles",
            dynamic=True,
        )
    
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("msg", label="The Message to Show")
        styles = types.Choices(label="Choose how to show the Error")
        show = styles.add_choice("show_output", label="Use the Show Output Operator")
        styles.add_choice("resolve_output", label="Execute + Resolve Output")
        inputs.enum("styles", styles.values(), default=show.value, view=styles)
        return types.Property(inputs, label="Error Examples")

    def execute(self, ctx):
        outputs = types.Object()
        outputs.str("msg", view=types.Error(label=ctx.params["msg"]))
        show_output = ctx.params["styles"] == "show_output"
        if show_output:
            ctx.trigger(
                "show_output",
                {
                    "outputs": types.Property(outputs).to_json()
                }
            )
        return {
            "msg": ctx.params["msg"]
        }
    
    def resolve_output(self, ctx):
        if ctx.params["styles"] == "resolve_output":
            outputs = types.Object()
            outputs.str("msg", view=types.Error(label=ctx.params["msg"]))
            return types.Property(outputs)

            

###
### Mutations
###
class SetFieldExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_set_field",
            label="Set Field",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        if (len(ctx.selected) > 0):
            inputs.str('msg', view=types.Notice(label=f"Update {len(ctx.selected)} Selected Samples"))
        else:
            inputs.str('msg', view=types.Notice(label=f"Update {len(ctx.view)} Samples"))
        fields = ctx.view.get_field_schema(flat=True)
        field_names = list(fields.keys())
        inputs.bool("use_custom", label="Use Custom Field")
        if (ctx.params.get("use_custom", False)):
            inputs.str("custom_field", label="Custom Field")
        else:
            inputs.enum("field", field_names, label="Field", view=types.Dropdown())
        inputs.str("value", label="Value")
        return types.Property(inputs)

    def execute(self, ctx):
        if (ctx.params.get("use_custom", False)):
            field = ctx.params.get("custom_field")
        else:
            field = ctx.params.get("field")
        value = ctx.params.get("value")
        view = ctx.view
        if (len(ctx.selected) > 0):
            view = ctx.dataset.select(ctx.selected)
        view.set_values(field, [value])
        ctx.trigger("reload_samples")
        return {"field": field, "updated": len(view)}
    
    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.int("updated", label="Updated")
        outputs.str("field", label="Field")
        return types.Property(outputs)
    
def register(p):
    p.register(SimpleInputExample)
    p.register(PlotExample)
    p.register(TableExample)
    p.register(InputListExample)
    p.register(ChoicesExample)
    p.register(ImageExample)
    p.register(SetFieldExample)
    p.register(ExampleSlideshow)
    p.register(ExampleShowOutput)
