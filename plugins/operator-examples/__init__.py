"""
Example operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import asyncio

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


class MessagesExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_messages",
            label="Examples: Messages",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        form_view = types.View(
            label="Form View Header", description="Form View Description"
        )
        inputs.message(
            "message", "Message", description="A Message Description"
        )
        warning = types.Warning(
            label="Notice Label", description="A Notice Description"
        )
        inputs.view("warning", warning)
        error = types.Error(
            label="Error Label", description="An Error Description"
        )
        inputs.view("error", error)
        return types.Property(inputs, view=form_view)

    def execute(self, ctx):
        return {}


class MarkdownExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_markdown",
            label="Examples: Markdown",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str(
            "markdown",
            label="Markdown",
            view=types.CodeView(language="markdown"),
        )
        return types.Property(inputs)

    def execute(self, ctx):
        return {"markdown": ctx.params["markdown"]}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("markdown", label="Markdown", view=types.MarkdownView())
        return types.Property(outputs)


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
        header = "Simple Input Example"
        return types.Property(inputs, view=types.View(label=header))

    def execute(self, ctx):
        return {"message": ctx.params["message"]}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("message", label="Message")
        header = "Simple Input Example: Success!"
        return types.Property(outputs, view=types.View(label=header))


class ChoicesExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_choices",
            label="Examples: Choices",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        radio_choices = types.RadioGroup()
        radio_choices.add_choice("choice1", label="Use Defaults")
        radio_choices.add_choice("choice2", label="Advanced")
        inputs.enum(
            "radio_choices",
            radio_choices.values(),
            default=radio_choices.choices[0].value,
            label="Radio Choices",
            view=radio_choices,
        )
        if ctx.params.get("radio_choices", False) == "choice2":
            dropdown_choices = types.Dropdown(label="Advanced Choices")
            dropdown_choices.add_choice("choice1", label="Choice 1")
            dropdown_choices.add_choice("choice2", label="Choice 2")
            dropdown_choices.add_choice("choice3", label="Choice 3")
            inputs.enum(
                "dropdown_choices",
                dropdown_choices.values(),
                default=dropdown_choices.choices[0].value,
                view=dropdown_choices,
            )
        return types.Property(inputs)

    def execute(self, ctx):
        return {
            "radio_choice": ctx.params.get("radio_choices", "None provided"),
            "dropdown_choice": ctx.params.get(
                "dropdown_choices", "None provided"
            ),
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
        return {
            "people": [
                person.get("first_name") for person in ctx.params["list"]
            ]
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.list("people", types.String(), label="People")
        return types.Property(outputs)


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
                    "x": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                    ],
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


class OutputStylesExample(foo.Operator):
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
        show = styles.add_choice(
            "show_output", label="Use the Show Output Operator"
        )
        styles.add_choice("resolve_output", label="Execute + Resolve Output")
        inputs.enum("styles", styles.values(), default=show.value, view=styles)
        return types.Property(inputs, label="Error Examples")

    def execute(self, ctx):
        outputs = types.Object()
        outputs.str("msg", view=types.Error(label=ctx.params["msg"]))
        show_output = ctx.params["styles"] == "show_output"
        if show_output:
            ctx.trigger(
                "show_output", {"outputs": types.Property(outputs).to_json()}
            )
        return {"msg": ctx.params["msg"]}

    def resolve_output(self, ctx):
        if ctx.params["styles"] == "resolve_output":
            outputs = types.Object()
            outputs.str("msg", view=types.Error(label=ctx.params["msg"]))
            return types.Property(outputs)


class ProgressExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_progress",
            label="Examples: Progress",
            execute_as_generator=True,
        )

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
                "results": {"percent_complete": i / MAX},
            }
            yield ctx.trigger("show_output", show_output_params)
            # simulate computation
            await asyncio.sleep(0.5)


class SetFieldExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_set_field",
            label="Examples: Set Field",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        if len(ctx.selected) > 0:
            inputs.str(
                "msg",
                view=types.Notice(
                    label=f"Update {len(ctx.selected)} Selected Samples"
                ),
            )
        else:
            inputs.str(
                "msg",
                view=types.Notice(label=f"Update {len(ctx.view)} Samples"),
            )
        fields = ctx.view.get_field_schema(flat=True)
        field_names = list(fields.keys())
        inputs.bool("use_custom", label="Use Custom Field")
        if ctx.params.get("use_custom", False):
            inputs.str("custom_field", label="Custom Field")
        else:
            inputs.enum(
                "field", field_names, label="Field", view=types.Dropdown()
            )
        inputs.str("value", label="Value")
        return types.Property(inputs)

    def execute(self, ctx):
        if ctx.params.get("use_custom", False):
            field = ctx.params.get("custom_field")
        else:
            field = ctx.params.get("field")
        value = ctx.params.get("value")
        view = ctx.view
        if len(ctx.selected) > 0:
            view = ctx.dataset.select(ctx.selected)
        for sample in view:
            sample.set_field(field, value)
            sample.save()
        ctx.trigger("reload_dataset")
        return {"field": field, "updated": len(view)}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.int("updated", label="Updated")
        outputs.str("field", label="Field")
        return types.Property(outputs)


class SettingsExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_settings",
            label="Examples: Settings",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        dropdown = types.AutocompleteView(label="Datasets")
        for dataset in fo.list_datasets():
            dropdown.add_choice(dataset, label=dataset)
        inputs.enum("dataset", dropdown.values(), required=True, view=dropdown)
        return types.Property(inputs)

    def execute(self, ctx):
        dataset = fo.load_dataset(ctx.params["dataset"])
        global_settings = fo.app_config.plugins or {}
        dataset_settings = dataset.app_config.plugins or {}
        settings = {**global_settings, **dataset_settings}
        dataset = ctx.params["dataset"]
        return {"settings": settings, "dataset": dataset}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("dataset", label="Dataset")
        outputs.obj("settings", label="Settings", view=types.JSONView())
        return types.Property(outputs)


class CustomViewExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_custom_view",
            label="Examples: Custom View",
        )

    def execute(self, ctx):
        return {}

    def resolve_input(self, ctx):
        inputs = types.Object()
        component = types.View(
            label="My custom component", component="ExampleCustomView"
        )
        inputs.define_property(
            "component",
            types.String(),
            view=component,
            invalid=True,
            error_message="Custom error message",
        )
        return types.Property(inputs)


class OpenHistogramsPanelExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_open_histograms_panel",
            label="Examples: Open Histograms Panel",
        )

    def resolve_placement(self, ctx):
        return types.Placement(
            # Display placement in the actions row of samples grid
            types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
            # Display a button as the placement
            types.Button(
                # label for placement button visible on hover
                label="Open Histograms Panel",
                # icon for placement button. If not provided, button with label
                # will be displayed
                icon="/assets/histograms.svg",
                # skip operator prompt when we do not require an input from the user
                prompt=False,
            ),
        )

    def execute(self, ctx):
        ctx.trigger(
            "open_panel",
            params=dict(name="Histograms", isActive=True, layout="horizontal"),
        )
        return {}


class FileDropzoneExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_file_dropzone",
            label="Examples: File Dropzone",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        ten_mb = 1024 * 1024 * 10
        file_drop = types.FileView(
            label="File Drop",
            max_size=ten_mb,
            max_size_error_message="File too large",
        )
        inputs.obj("file", view=file_drop)
        return types.Property(inputs)

    def execute(self, ctx):
        return {"file": ctx.params["file"]}

    def resolve_output(self, ctx):
        outputs = types.Object()
        file_obj = types.Object()
        file_obj.str("name", label="Name")
        file_obj.str("type", label="Type")
        file_obj.int("size", label="Size")
        # also available:
        # - file['contents'] which is a base64 encoded string
        # - file['last_modified'] which is ms since epoch
        outputs.add_property("file", types.Property(file_obj))
        return types.Property(outputs)


class SelectedSamplesExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_selected_samples",
            label="Examples: Selected Samples",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message(
            "Number of Selected Samples",
            label=f"Number of Selected Samples: {len(ctx.selected)}",
        )
        return types.Property(inputs)

    def execute(self, ctx):
        return {"num_selected_samples": len(ctx.selected)}

    def resolve_output(self, ctx):
        outputs = types.Object()

        outputs.message(
            "Number of Selected Samples",
            label=f"Number of Selected Samples: {len(ctx.selected)}",
        )

        outputs.int("num_selected_samples", label="Num Selected Samples")

        return types.Property(outputs)


class SelectedLabelsExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_selected_labels",
            label="Examples: Selected Labels",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message(
            "Number of Selected Labels",
            label=f"Number of Selected Label: {len(ctx.selected_labels)}",
        )
        return types.Property(inputs)

    def execute(self, ctx):
        label_fields = [field["field"] for field in ctx.selected_labels]
        return {
            "num_selected_labels": len(ctx.selected_labels),
            "label_fields": label_fields,
        }

    def resolve_output(self, ctx):
        outputs = types.Object()

        outputs.message(
            "Number of Selected Labels",
            label=f"Number of Selected Label: {len(ctx.selected_labels)}",
        )

        outputs.int("num_selected_labels", label="Num Selected Labels")
        outputs.list("label_fields", types.String(), label="Label Fields")

        return types.Property(outputs)


class CurrentSampleExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_current_sample",
            label="Examples: Current Sample",
        )

    def execute(self, ctx):
        if ctx.current_sample is None:
            return {
                "result": {
                    "message": (
                        "No sample provided. Select a sample to see the result"
                    )
                }
            }

        sample = ctx.dataset[ctx.current_sample]

        if ctx.dataset.media_type == "group":
            group_field = ctx.dataset.group_field
            current_group = sample[group_field].id
        else:
            current_group = None

        return {
            "result": {
                "current_sample": ctx.current_sample,
                "sample": sample.to_dict() if sample else None,
                "current_group": current_group,
            }
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.obj("result", label="Result", view=types.JSONView())
        return types.Property(outputs)


class SetViewExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_set_view",
            label="Examples: Set View",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message(
            "Set View",
            label="Set View",
        )
        return types.Property(inputs)

    def execute(self, ctx):
        view = ctx.dataset.take(10)
        ctx.ops.set_view(view=view)


class DelegatedExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_delegated",
            label="Examples: Delegated",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message(
            "Delegated Operator",
            label="Delegated Operator",
            description=(
                "This operation will be queued. Launch from CLI with"
                "`fiftyone delegated launch`"
            ),
        )
        return types.Property(inputs)

    def resolve_delegation(self, ctx):
        return True

    def execute(self, ctx):
        import time

        for i in range(10):
            time.sleep(1)
            print(f"Delegated execution in progress: {i+1}0% Complete")


class SecretsExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_secrets",
            label="Examples: Secrets",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message(
            "Secrets Operator",
            label="Secrets Operator",
            description=(
                "This operator allows you to test the `secrets` feature in "
                "delegated operators. Export the secret `FIFTYONE_EXAMPLE_SECRET` "
                "to your environment (with whatever value you'd like!) and "
                "launch this operator with `fiftyone delegated launch`"
            ),
        )
        return types.Property(inputs)

    def resolve_delegation(self, ctx):
        return True

    def execute(self, ctx):
        if "FIFTYONE_EXAMPLE_SECRET" in ctx.secrets:
            print("The delegated operator has access to the secret!")
        else:
            print("The delegated operator does not have access to the secret.")


class LazyFieldExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_lazy_field",
            label="Examples: Lazy Field",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        url = ctx.params.get("url", "No value provided for URL yet")
        inputs = types.Object()
        inputs.str("url", label="URL", view=types.LazyFieldView())
        inputs.view("url-preview", view=types.Notice(label=url))
        return types.Property(inputs)

    def execute(self, ctx):
        return {"url": ctx.params.get("url", "No value provided")}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("url", label="URL")
        return types.Property(outputs)


class TargetViewExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_target_view",
            label="Examples: Target View",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.view_target(ctx)
        return types.Property(inputs)

    def execute(self, ctx):
        target_view = ctx.target_view()
        return {"target_view": target_view.count()}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.int("target_view", label="Target View")
        return types.Property(outputs)


class PythonViewExample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_python_view",
            label="Examples: Python View",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        src = ctx.params.get("python", None)
        py = inputs.str("python", label="Python", required=True)
        if src and not src.startswith("view."):
            inputs.str("error", label="Error", view=types.Error())
            py.invalid = True
            py.error_message = "Python must start with view"

        return types.Property(inputs)

    def execute(self, ctx):
        src = ctx.params.get("python", None)
        if src is None:
            return {}

        view = eval(src, {"view": ctx.dataset.view()})

        ctx.ops.set_view(view=view)


class ExampleComplexExecution(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_complex_execution",
            label="Example Complex Execution",
            allow_immediate_execution=True,
            allow_delegated_execution=True,
            default_choice_to_delegated=True,
            resolve_execution_options_on_change=False,
        )

    def __call__(
        self,
        sample_collection,
        message=None,
        delegate=False,
        delegation_target=None,
    ):
        """Illustrates a complex operation that can be run immediately or
        delegated.

        Example usage::

            import fiftyone as fo
            import fiftyone.operators as foo
            import fiftyone.zoo as foz

            dataset = foz.load_zoo_dataset("quickstart")
            complex_exec = foo.get_operator("@voxel51/operator-examples/example_complex_execution")

            # Run immediately
            complex_exec(dataset, message="Running immediately")

            # Schedule to run on an orchestrator
            complex_exec(dataset, delegate=True, message="Running on orchestrator")

        Args:
            delegate (False): whether to delegate execution
            delegation_target (None): an optional orchestrator on which to
                schedule the operation, if it is delegated
        """
        if isinstance(sample_collection, fo.DatasetView):
            ctx = dict(view=sample_collection)
        else:
            ctx = dict(dataset=sample_collection)

        return foo.execute_operator(
            self.uri,
            ctx,
            params=dict(message=message),
            request_delegation=delegate,
            delegation_target=delegation_target,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("message", label="Message")
        return types.Property(inputs)

    def execute(self, ctx):
        if ctx.delegated:
            print("Running on orchestrator")
        else:
            print("Running in-process")
        print(f"Message: {ctx.params['message']}")


def register(p):
    p.register(MessagesExample)
    p.register(SimpleInputExample)
    p.register(PlotExample)
    p.register(TableExample)
    p.register(InputListExample)
    p.register(ChoicesExample)
    p.register(ImageExample)
    p.register(SetFieldExample)
    p.register(OutputStylesExample)
    p.register(ProgressExample)
    p.register(SettingsExample)
    p.register(MarkdownExample)
    p.register(CustomViewExample)
    p.register(OpenHistogramsPanelExample)
    p.register(SelectedSamplesExample)
    p.register(SelectedLabelsExample)
    p.register(CurrentSampleExample)
    p.register(SetViewExample)
    p.register(DelegatedExample)
    p.register(SecretsExample)
    p.register(FileDropzoneExample)
    p.register(LazyFieldExample)
    p.register(TargetViewExample)
    p.register(PythonViewExample)
    p.register(ExampleComplexExecution)
